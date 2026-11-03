# Lean 4 Trade Assessment API

This package contains a production-ready REST API that wraps your assessment kernel. The API accepts JSON trade data, executes your kernel, and returns assessment results. **Kernel logic is protected and not exposed through the API.**

## Quick Summary

✅ **What's Included:**
- REST API with FastAPI (Python)
- JSON input/output format
- API key authentication for security
- **Kernel IP Protection** - Logic not exposed in responses or errors
- Docker container for deployment
- Example client code
- Full documentation
- Deployment checklist for SPV

✅ **What You Need:**
- Docker & Docker Compose (for deployment)
- Your compiled assessment kernel (`Lean4.exe`)
- Secure API keys (auto-generated)

✅ **What to Do:** 
1. Copy your kernel (`Lean4.exe`) to the root directory
2. Run `api/start.bat` (Windows) or `api/start.sh` (Linux/Mac)
3. Generate and configure API keys
4. API will be available at `http://localhost:8000`

## Structure

```
├── api/                      # API application (this is what gets deployed)
│   ├── main.py              # FastAPI application
│   ├── requirements.txt      # Python dependencies
│   ├── Dockerfile           # Container image definition
│   ├── docker-compose.yml   # Container orchestration
│   ├── .env.example         # Configuration template
│   ├── generate_keys.py     # API key generator (run this first)
│   ├── example_client.py    # Example client code
│   ├── README.md            # Full API documentation
│   ├── start.sh             # Linux/Mac startup
│   └── start.bat            # Windows startup
├── DEPLOYMENT_CHECKLIST.md  # SPV deployment guide
└── Lean4/                   # Your Lean 4 kernel source
```

## Getting Started

### Step 1: Generate API Keys

```bash
python api/generate_keys.py --count 1
```

This creates a secure API key. Save it somewhere safe.

### Step 2: Configure

Edit `api/.env.example`, then save as `.env`:
```
AUTHORIZED_API_KEYS=<your-generated-key>
```

Note: Kernel path and timeout are hardcoded for security.

### Step 3: Start

**Windows:**
```bash
api\start.bat
```

**Linux/Mac:**
```bash
bash api/start.sh
```

### Step 4: Test

Visit `http://localhost:8000/docs` for interactive API documentation

Or use the example client:
```bash
python api/example_client.py
```

## API Usage Example

```python
import requests

# Test a trade
response = requests.post(
    "http://localhost:8000/assess",
    headers={"X-API-Key": "your-api-key"},
    json={
        "trade_id": "TRD-001",
        "symbol": "EURUSD",
        "quantity": 1000000,
        "price": 1.0850,
        "direction": "BUY"
    }
)

result = response.json()
# Response contains: trade_id, status ("approved"/"rejected"/"flagged"), timestamp, and error (if any)
print(f"Status: {result['status']}")
print(f"Timestamp: {result['timestamp']}")  
# Kernel logic is not exposed in the response
```

## For SPV Deployment

The SPV responsible for deployment should:

1. **Review** `DEPLOYMENT_CHECKLIST.md` for security and deployment steps
2. **Generate** secure API keys with `api/generate_keys.py`
3. **Store** API keys in a secrets manager (Azure KeyVault, AWS Secrets Manager, etc.)
4. **Deploy** using Docker Compose to your secure server
5. **Configure** HTTPS reverse proxy (nginx/traefik) for TLS encryption
6. **Monitor** logs and API health
7. **Maintain** according to the checklist schedule

## Key Features

🔐 **Security**
- API key authentication (header: `X-API-Key`)
- Docker container runs as non-root
- Minimal permissions, no privileged mode
- Input validation on all requests
- Error messages don't expose system details

📊 **Functionality**
- Single trade assessment: POST /assess
- Batch assessment: POST /batch-assess
- Health check: GET /health
- Full JSON request/response

📦 **Deployment**
- One-command startup (Docker)
- Containerized for consistent environments
- Ready for cloud deployments
- Includes monitoring/logging

## Documentation

- **API Docs**: `api/README.md` (full API documentation)
- **Deployment Guide**: `DEPLOYMENT_CHECKLIST.md` (for SPV)
- **Example Client**: `api/example_client.py` (shows how to use the API)
- **Interactive Docs**: Available at `http://localhost:8000/docs` when running

## Troubleshooting

### API won't start
```bash
docker-compose -f api/docker-compose.yml logs
```

### Lean kernel not found
Ensure `Lean4.exe` is in the root directory and update `LEAN_EXECUTABLE` in `.env`

### Connection errors
Make sure Docker is running and port 8000 isn't in use

### Timeout errors
Increase `KERNEL_TIMEOUT` in `.env` if your kernel takes longer

See `api/README.md` for detailed troubleshooting.

## Security Notes

⚠️ **Important:**
- Never commit `.env` to git (use `.env.example` as template)
- Generate new API keys for production (use `generate_keys.py`)
- Store API keys in a secrets manager, not in code
- Use HTTPS in production (configure reverse proxy)
- Keep Docker images updated
- Monitor logs for suspicious activity
- Rotate API keys regularly

## Support

For issues:
1. Check logs: `docker logs trade-assessment-api`
2. Test health: `curl http://localhost:8000/health`
3. Review `api/README.md` for detailed documentation
4. See `DEPLOYMENT_CHECKLIST.md` for deployment guidance
