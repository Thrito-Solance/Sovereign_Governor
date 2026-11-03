# Trade Assessment API

A production-ready REST API that accepts trade data in JSON format and runs your assessment kernel. Includes authentication and Docker packaging for secure deployment.

## Features

✅ **RESTful API** - Clean, documented endpoints  
✅ **JSON Input/Output** - Easy integration with your systems  
✅ **API Key Authentication** - Secure access control  
✅ **Kernel Protection** - Proprietary kernel logic is not exposed  
✅ **Batch Processing** - Assess multiple trades efficiently  
✅ **Docker Ready** - One-command deployment  
✅ **Minimal Logging** - Only essential operational events logged  
✅ **Health Checks** - Built-in API health endpoint  
✅ **Error Handling** - Safe error responses (no technical details leaked)  

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Your compiled assessment kernel (`Lean4.exe`)
- Python 3.11+ (for local development)

### 1. Prepare

Copy the API configuration template:
```bash
cp api/.env.example .env
```

Edit `.env` and update only:
```
AUTHORIZED_API_KEYS=your-secure-key-1,your-secure-key-2
```

Note: Kernel executable path and timeout are hardcoded for security.

### 2. Generate API Keys

```bash
python api/generate_keys.py --count 1
```

This creates cryptographically secure keys. Add them to your `.env` file.

### 3. Start the API

**On Windows:**
```bash
api\start.bat
```

**On Linux/Mac:**
```bash
bash api/start.sh
```

The API will start on `http://localhost:8000`

### 4. Test the API

Access the interactive documentation:
```
http://localhost:8000/docs
```

Or use the example client:
```bash
python api/example_client.py
```

## API Endpoints

### Health Check
```
GET /health
```
Returns API status and version.

### Assess Trade
```
POST /assess
Headers: X-API-Key: <your-api-key>
Content-Type: application/json

Body:
{
  "trade_id": "TRD-001",
  "symbol": "EURUSD",
  "quantity": 1000000,
  "price": 1.0850,
  "direction": "BUY",
  "counterparty": "BANK-A",
  "metadata": {"key": "value"}
}

Response:
{
  "trade_id": "TRD-001",
  "status": "approved",
  "timestamp": "2024-02-24T10:30:00",
  "error": null
}
```

**Note**: Only the assessment decision (`status`) is returned. Kernel implementation details are proprietary and intentionally not exposed.

### Batch Assessment
```
POST /batch-assess
Headers: X-API-Key: <your-api-key>
Content-Type: application/json

Body:
[
  {trade_id: "TRD-001", symbol: "EURUSD", ...},
  {trade_id: "TRD-002", symbol: "GBPUSD", ...}
]
```

## Configuration

The API requires only one configuration setting:

| Setting | Description |
|---------|-------------|
| `AUTHORIZED_API_KEYS` | Comma-separated API keys (required) |

All other settings are **hardcoded for security**:
- Kernel executable path is fixed (cannot be changed)
- Kernel timeout is fixed at 30 seconds
- Logging is minimal (only operational events, no kernel details)

## Deployment

### Docker Compose (Recommended)

```bash
docker-compose -f api/docker-compose.yml up -d
```

View logs:
```bash
docker-compose -f api/docker-compose.yml logs -f
```

Stop:
```bash
docker-compose -f api/docker-compose.yml down
```

### Docker Manual Build

```bash
# Build image
docker build -f api/Dockerfile -t trade-api:latest .

# Run container
docker run -p 8000:8000 \
  -e AUTHORIZED_API_KEYS="your-key-1,your-key-2" \
  -e LEAN_EXECUTABLE="./Lean4.exe" \
  trade-api:latest
```

### Production Deployment

For production deployment to a secure server:

1. **Update `.env` with secure API keys:**
   ```bash
   python api/generate_keys.py --count 3
   ```

2. **Use a secrets manager** (Azure KeyVault, AWS Secrets Manager, HashiCorp Vault)
   - Store API keys securely
   - Inject at runtime

3. **Set up HTTPS:**
   - Use a reverse proxy (nginx, traefik)
   - Install SSL certificate
   - Configure in your infrastructure

4. **Monitor and log:**
   - Collect logs from containers
   - Monitor API metrics
   - Set up alerts

5. **Example with nginx reverse proxy:**

   ```nginx
   server {
       listen 443 ssl http2;
       server_name api.example.com;

       ssl_certificate /etc/certificates/cert.pem;
       ssl_certificate_key /etc/certificates/key.pem;

       location / {
           proxy_pass http://localhost:8000;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

## Client Examples

### Python
```python
import requests

headers = {"X-API-Key": "your-api-key"}
trade_data = {
    "trade_id": "TRD-001",
    "symbol": "EURUSD",
    "quantity": 1000000,
    "price": 1.0850,
    "direction": "BUY"
}

response = requests.post(
    "http://localhost:8000/assess",
    json=trade_data,
    headers=headers
)

result = response.json()
print(f"Status: {result['status']}")
```

### cURL
```bash
curl -X POST http://localhost:8000/assess \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "trade_id": "TRD-001",
    "symbol": "EURUSD",
    "quantity": 1000000,
    "price": 1.0850,
    "direction": "BUY"
  }'
```

### JavaScript/Node.js
```javascript
const response = await fetch('http://localhost:8000/assess', {
  method: 'POST',
  headers: {
    'X-API-Key': 'your-api-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    trade_id: 'TRD-001',
    symbol: 'EURUSD',
    quantity: 1000000,
    price: 1.0850,
    direction: 'BUY'
  })
});

const result = await response.json();
console.log(`Status: ${result.status}`);
```

## Security Features

🔒 **Kernel Protection** - Proprietary kernel logic is not exposed  
🔒 **API Key Authentication** - Required header: `X-API-Key`  
🔒 **Minimal Logging** - Only operational events logged, no kernel details  
🔒 **Safe Error Messages** - Errors never expose internal implementation  
🔒 **Non-root User** - Runs in Docker as unprivileged user  
🔒 **Minimal Permissions** - Only necessary Linux capabilities  
🔒 **Input Validation** - Pydantic models validate all inputs  
🔒 **Hardcoded Configuration** - Critical settings cannot be changed at runtime  
🔒 **Timeout Protection** - Kernel execution has fixed timeout limits  

### What the API Does NOT Expose

- ❌ Raw kernel output
- ❌ Kernel logic or algorithms
- ❌ Detailed error messages revealing internals
- ❌ Input/output logging
- ❌ Kernel executable details  

## Troubleshooting

### API won't start
```bash
docker-compose -f api/docker-compose.yml logs
```

### "Lean executable not found"
- Ensure `Lean4.exe` is in the root directory
- Verify `LEAN_EXECUTABLE` in `.env` is correct

### Timeout errors
- Increase `KERNEL_TIMEOUT` in `.env`
- Check if Lean kernel is responding

### Connection refused
- Ensure Docker container is running: `docker ps`
- Check port 8000 is not in use: `netstat -tuln | grep 8000`

## Development

For local development without Docker:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r api/requirements.txt

# Run API
python -m uvicorn api.main:app --reload --port 8000
```

## Files Structure

```
Lean4/
├── api/
│   ├── main.py                 # Main API application
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile             # Container definition
│   ├── docker-compose.yml     # Container orchestration
│   ├── .env.example           # Configuration template
│   ├── generate_keys.py       # API key generator
│   ├── example_client.py      # Example client code
│   ├── start.sh               # Linux startup script
│   └── start.bat              # Windows startup script
├── Lean4.lean                 # Main Lean kernel
├── Lean4/
│   └── Basic.lean             # Lean modules
├── lakefile.toml              # Lake configuration
└── README.md                  # This file
```

## Support & Documentation

- **API Docs**: http://localhost:8000/docs (interactive Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc format)
- **Lean4 Guide**: https://lean-lang.org/lean4/doc/

## License

This API wrapper is provided as-is for use with your Lean 4 kernel.

## Maintenance

The SPV responsible for deployment should:

1. Keep API keys secure and rotated
2. Monitor logs for errors and suspicious activity
3. Update base image regularly: `docker pull python:3.11-slim`
4. Test with sample trades regularly
5. Have a backup of the Lean executable
