# Deployment Checklist for SPV

Complete this checklist before deploying the Trade Assessment API to a secure server.

## Pre-Deployment Setup

- [ ] **Generate Secure API Keys**
  ```bash
  python api/generate_keys.py --count 2-3
  ```
  Save these keys securely (password manager, vault, etc.)

- [ ] **Prepare Assessment Kernel**
  - Ensure your kernel is compiled and placed as `Lean4.exe` in root directory
  - Test locally that it executes correctly with sample trade data

- [ ] **Review Configuration**
  - Update `.env` with your API keys only
  - Verify kernel executable is in the correct location
  - Note: Kernel path and timeout are hardcoded for security

## Security Checklist

- [ ] **API Keys**
  - Keys are cryptographically secure (use generate_keys.py)
  - Never commit `.env` file to git
  - Store in secrets manager (Azure KeyVault, AWS Secrets Manager, etc.)

- [ ] **Kernel Protection**
  - Kernel executable path is hardcoded (cannot be changed)
  - API does not expose kernel logic or internal behavior
  - Kernel output is processed only for decision extraction
  - Error messages never leak implementation details

- [ ] **Network Security**
  - API runs on secure server (not public internet)
  - Route remote access through an HTTPS/TLS reverse proxy
  - Keep the API's published port bound to loopback; do not expose port 8000 directly
  - Disable HTTP (enforce HTTPS only)
  - Configure firewall rules (whitelist IPs if needed)
  - POST, PUT, and PATCH requests must include exactly one valid `Content-Length` header; chunked or conflicting framing is rejected
  - Requests over 10 MiB are rejected with HTTP 413; requests without `Content-Length` are rejected with HTTP 411

- [ ] **Docker Security**
  - Image runs as non-root user (appuser)
  - Minimal permissions (no unnecessary capabilities)
  - No privileged mode
  - Kernel executable is not extractable from logs or responses

- [ ] **Monitoring & Logging**
  - Container logs are persisted
  - Note: Logging is minimal by design - only operational events logged
  - Set up log aggregation (ELK, Splunk, CloudWatch, etc.)
  - Configure alerts for errors

- [ ] **Security Testing** (BEFORE PRODUCTION - ALL REQUIRED)
  - Run adversary testing suite: `python test_security.py`
    - All 18 tests must pass
    - Documents 10 vulnerabilities and verifies patches
  - Run epsilon perturbation tests: `python test_epsilon_perturbations.py`
    - All 40 boundary value tests must pass
    - Ensures constraints are airtight at edges
  - Run extreme scenario tests: `python test_extreme_scenarios.py`
    - All 35 creative adversarial tests must pass
    - Tests IEEE 754 edge cases, Unicode tricks, type confusion, concurrency

## Deployment Steps

### On Secure Server

1. **Copy API Files**
   ```bash
   scp -r api/ user@server:/path/to/api
   scp Lean4.exe user@server:/path/to/api
   ```

2. **Set Up Environment**
   ```bash
   ssh user@server
   cd /path/to/api
   cp .env.example .env
   # Edit .env with production values, especially AUTHORIZED_API_KEYS
   ```

3. **Start Service**
   ```bash
   docker-compose -f docker-compose.yml up -d
   ```

4. **Verify Health**
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status": "healthy", ...}
   ```

5. **Pre-Deployment Security Verification** (REQUIRED)
   
   Run all four automated security test suites (111 tests):
   
   ```bash
   # Test 1: Paradox boundary tests (18 tests, ~1 minute)
   python test_paradox_boundaries.py http://localhost:8000 <api-key>
   # Identifies logical contradictions and impossible states
   
   # Test 2: Adversary testing suite (18 tests, ~30 seconds)
   python test_security.py http://localhost:8000 <api-key>
   # Verifies patches for 10 identified vulnerabilities
   
   # Test 3: Epsilon perturbation tests (40 tests, ~1 minute)
   python test_epsilon_perturbations.py http://localhost:8000 <api-key>
   # Boundary value analysis - ensures constraints are airtight
   
   # Test 4: Extreme scenario tests (35 tests, ~2 minutes)
   python test_extreme_scenarios.py http://localhost:8000 <api-key>
   # Creative adversarial attacks - IEEE 754, Unicode, type confusion, etc.
   ```
   
   **All 111 tests MUST pass before production.** If any fail:
   1. Review the error message
   2. Identify the constraint that failed
   3. Verify the corresponding validation in api/main.py
   4. Fix and re-run tests
   
   See [PARADOX_BOUNDARY_ANALYSIS.md](PARADOX_BOUNDARY_ANALYSIS.md), [SECURITY_ASSESSMENT.md](SECURITY_ASSESSMENT.md), [EPSILON_TESTING_GUIDE.md](EPSILON_TESTING_GUIDE.md), and [EXTREME_TESTING_GUIDE.md](EXTREME_TESTING_GUIDE.md) for details.

6. **Test with Example Trade**
   ```bash
   curl -X POST http://localhost:8000/assess \
     -H "X-API-Key: <your-key>" \
     -H "Content-Type: application/json" \
     -d '{"trade_id": "TEST-001", "symbol": "EURUSD", "quantity": 1000000, "price": 1.0850, "direction": "BUY"}'
   ```

### Required for Remote Access: Set Up Reverse Proxy (HTTPS)

The Compose configuration publishes the API only on `127.0.0.1:8000`. Keep that loopback-only binding and route remote traffic through the TLS reverse proxy. Do not change the binding to `0.0.0.0` or publish port 8000 directly.

**Using nginx:**

```nginx
# /etc/nginx/sites-available/trade-api
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $host;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name api.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

Enable the config:
```bash
sudo ln -s /etc/nginx/sites-available/trade-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Post-Deployment

- [ ] **Monitor First 24 Hours**
  - Check logs regularly
  - Test with sample trades
  - Monitor performance/response times
  - No unexpected errors

- [ ] **Set Up Automated Backups**
  - Backup API keys (encrypted)
  - Backup logs
  - Test restore procedures

- [ ] **Communication to Clients**
  - Provide API endpoint URL
  - Provide documentation
  - Provide example code (see `example_client.py`)
  - Share API keys securely (never via email)

- [ ] **Documentation**
  - Store deployment procedures
  - Document API key rotation schedule
  - Document incident response procedures
  - Keep runbook for troubleshooting

## Maintenance Schedule

- **Daily**: Monitor logs, health checks
- **Weekly**: Review API usage/performance
- **Monthly**: Rotate API keys, update dependencies
- **Quarterly**: Security audit, penetration testing
- **Annually**: Full infrastructure review

## Troubleshooting Guide

See `api/README.md` for detailed troubleshooting.

Common issues:
- **Container won't start**: Check logs with `docker logs trade-assessment-api`
- **Timeout errors**: Increase `KERNEL_TIMEOUT` in `.env`
- **Authentication failures**: Verify API key in `X-API-Key` header
- **Lean executable not found**: Verify `LEAN_EXECUTABLE` path and permissions

## Rollback Procedure

If issues occur:

```bash
# Stop the running container
docker-compose -f api/docker-compose.yml down

# Check logs of last run
docker-compose -f api/docker-compose.yml logs

# If needed, rebuild from scratch
docker-compose -f api/docker-compose.yml build --no-cache
docker-compose -f api/docker-compose.yml up -d
```

## Support Contact

For technical issues:
- Review logs: `docker-compose logs -f`
- Check health: `curl http://localhost:8000/health`
- Inspect container: `docker exec -it trade-assessment-api /bin/bash`
