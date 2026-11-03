"""
Trade Assessment API
Accepts trade data in JSON format and runs the assessment kernel.

KERNEL PROTECTION: This API exposes only results. Internal kernel logic is proprietary
and intentionally not exposed through API responses or error messages.
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from starlette.responses import JSONResponse
from typing import Optional, Dict, Any
import subprocess
import json
import os
import logging
from datetime import datetime
import secrets

# Define request size limit (10MB)
MAX_REQUEST_SIZE_BYTES = 10 * 1024 * 1024

# Configure logging - REDACTED MODE
# Only logs critical operational events, not kernel inputs/outputs
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Trade Assessment API",
    description="Trade assessment API with secure authentication",
    version="1.0.0"
)

# ============================================================================
# MIDDLEWARE - SECURITY HARDENING
# ============================================================================

@app.middleware("http")
async def request_size_limit_middleware(request: Request, call_next):
    """Enforce maximum request size to prevent DOS attacks"""
    if request.method in ("POST", "PUT", "PATCH"):
        content_lengths = request.headers.getlist("content-length")
        if not content_lengths:
            return JSONResponse(
                status_code=status.HTTP_411_LENGTH_REQUIRED,
                content={"error": "Content-Length header is required"}
            )
        if len(content_lengths) != 1 or request.headers.get("transfer-encoding"):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid request framing"}
            )

        content_length = content_lengths[0]
        if not content_length.isascii() or not content_length.isdigit():
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Invalid Content-Length header"}
            )
        normalized_length = content_length.lstrip("0") or "0"
        max_request_size = str(MAX_REQUEST_SIZE_BYTES)
        if (
            len(normalized_length) > len(max_request_size)
            or (
                len(normalized_length) == len(max_request_size)
                and normalized_length > max_request_size
            )
        ):
            return JSONResponse(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                content={"error": "Payload exceeds maximum allowed size of 10 MB"}
            )
    
    return await call_next(request)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Hardcoded kernel executable - not configurable to prevent unauthorized usage
KERNEL_EXECUTABLE = os.path.join(os.path.dirname(__file__), "..", "Lean4.exe")
KERNEL_TIMEOUT = 30  # seconds - not configurable for security

# Security: Load and validate API keys
_api_keys_env = os.getenv("AUTHORIZED_API_KEYS", "").strip()
if not _api_keys_env:
    raise ValueError("FATAL: AUTHORIZED_API_KEYS environment variable is not set or empty. Cannot start.")
AUTHORIZED_API_KEYS = set(k.strip() for k in _api_keys_env.split(",") if k.strip())
if not AUTHORIZED_API_KEYS:
    raise ValueError("FATAL: No valid API keys found after parsing AUTHORIZED_API_KEYS.")

# Security: Input constraints
MAX_TRADE_ID_LENGTH = 100
MAX_SYMBOL_LENGTH = 20
MAX_COUNTERPARTY_LENGTH = 100
MAX_BATCH_SIZE = 100  # Max trades per batch request
MAX_METADATA_DEPTH = 3  # Max nesting level in metadata JSON
MAX_QUANTITY = 1e15  # Practical upper bound for quantities
MAX_PRICE = 1e10  # Practical upper bound for prices
MAX_STRING_LENGTH_FOR_METADATA_VALUES = 1000  # Per metadata value


# ============================================================================
# DATA MODELS
# ============================================================================

class TradeData(BaseModel):
    """Trade data input model with validation constraints"""
    trade_id: str = Field(..., description="Unique trade identifier", min_length=1, max_length=MAX_TRADE_ID_LENGTH)
    symbol: str = Field(..., description="Trading symbol/pair", min_length=1, max_length=MAX_SYMBOL_LENGTH)
    quantity: float = Field(..., gt=0, le=MAX_QUANTITY, description="Trade quantity")
    price: float = Field(..., gt=0, le=MAX_PRICE, description="Trade price")
    direction: str = Field(..., pattern="^(BUY|SELL)$", description="Trade direction")
    counterparty: Optional[str] = Field(default=None, description="Counterparty identifier", max_length=MAX_COUNTERPARTY_LENGTH)
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional trade metadata")
    
    @validator("metadata", pre=True, always=True)
    def validate_metadata(cls, v):
        """Validate metadata doesn't have deeply nested structures or huge values"""
        if v is None:
            return None
        
        def check_depth(obj, depth=0):
            if depth > MAX_METADATA_DEPTH:
                raise ValueError(f"Metadata nesting exceeds maximum depth of {MAX_METADATA_DEPTH}")
            if isinstance(obj, dict):
                for k, val in obj.items():
                    if not isinstance(k, str) or len(k) > 100:
                        raise ValueError("Metadata keys must be strings under 100 characters")
                    check_depth(val, depth + 1)
                    # Check value size
                    if isinstance(val, str) and len(val) > MAX_STRING_LENGTH_FOR_METADATA_VALUES:
                        raise ValueError(f"Metadata string values must be under {MAX_STRING_LENGTH_FOR_METADATA_VALUES} characters")
            elif isinstance(obj, list):
                raise ValueError("Metadata lists are not allowed")
            return v
        
        check_depth(v)
        return v


class AssessmentResult(BaseModel):
    """Assessment result output model - kernel internals are redacted"""
    trade_id: str
    status: str  # "approved", "rejected", "flagged" - only the decision is exposed
    timestamp: str
    error: Optional[str] = None  # Only generic errors, never expose kernel details


# ============================================================================
# AUTHENTICATION
# ============================================================================

async def verify_api_key(x_api_key: str = Header(...)) -> str:
    """
    Verify incoming API key with timing attack protection.
    
    Uses constant-time comparison to prevent timing attacks.
    No details logged to protect API keys.
    """
    if not x_api_key or not isinstance(x_api_key, str):
        logger.warning("Invalid API key format")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Use constant-time comparison to prevent timing attacks
    # Compare against a randomly selected key to avoid timing leaks
    is_valid = any(
        secrets.compare_digest(x_api_key, valid_key) if valid_key else False
        for valid_key in AUTHORIZED_API_KEYS
    )
    
    if not is_valid:
        logger.warning("Unauthorized access attempt")
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    return x_api_key


# ============================================================================
# KERNEL EXECUTION
# ============================================================================

def execute_kernel(trade_data: TradeData) -> str:
    """
    Execute assessment kernel with trade data.
    
    Returns: Status string only ("approved", "rejected", or "flagged")
    Kernel implementation details are intentionally not exposed.
    
    Args:
        trade_data: Trade data to assess
        
    Returns:
        Status string ("approved", "rejected", "flagged")
    """
    # Prepare JSON input without logging
    kernel_input = json.dumps({
        "trade_id": trade_data.trade_id,
        "symbol": trade_data.symbol,
        "quantity": trade_data.quantity,
        "price": trade_data.price,
        "direction": trade_data.direction,
        "counterparty": trade_data.counterparty,
        "metadata": trade_data.metadata
    })
    
    try:
        # Execute kernel with strict timeout
        result = subprocess.run(
            [KERNEL_EXECUTABLE],
            input=kernel_input,
            capture_output=True,
            text=True,
            timeout=KERNEL_TIMEOUT
        )
        
        # Process output - only extract the status
        if result.returncode != 0:
            logger.error(f"Kernel error for trade {trade_data.trade_id}")
            return "rejected"  # Failed kernel execution = reject
        
        try:
            # Parse kernel output to extract status
            output = json.loads(result.stdout.strip())
            
            # Extract status from kernel output
            # Kernel must return {"status": "approved|rejected|flagged", ...other fields}
            if isinstance(output, dict) and "status" in output:
                status = output["status"]
                if status in ("approved", "rejected", "flagged"):
                    return status
            
            # Fallback: if output contains decision markers, use them
            # But don't expose what those markers are
            return "flagged"  # Unknown format = flag for review
            
        except (json.JSONDecodeError, KeyError):
            logger.error(f"Kernel output parse error for trade {trade_data.trade_id}")
            return "flagged"  # Unparseable = flag for review
        
    except subprocess.TimeoutExpired:
        logger.error(f"Kernel timeout for trade {trade_data.trade_id}")
        return "flagged"  # Timeout = flag for manual review
    
    except FileNotFoundError:
        logger.error("Kernel executable not found")
        return "rejected"  # Can't execute = reject
    
    except Exception as e:
        logger.error(f"Kernel execution error for trade {trade_data.trade_id}")
        return "rejected"  # Any error = reject




# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check(api_key: str = Depends(verify_api_key)):
    """Health check endpoint - requires authentication"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.post("/assess", response_model=AssessmentResult)
async def assess_trade(
    trade_data: TradeData,
    api_key: str = Depends(verify_api_key)
) -> AssessmentResult:
    """
    Assess a trade.
    
    **Authentication**: Required header: `X-API-Key: <your-api-key>`
    
    **Input**: Trade data in JSON format
    - trade_id: Unique identifier for the trade
    - symbol: Trading pair/symbol
    - quantity: Trade quantity (must be > 0)
    - price: Trade price (must be > 0)
    - direction: "BUY" or "SELL"
    - counterparty: (optional) Counterparty identifier
    - metadata: (optional) Additional data
    
    **Output**: Assessment decision
    - status: "approved", "rejected", or "flagged"
    
    **Note**: Kernel implementation is proprietary. Only the assessment result is returned.
    """
    timestamp = datetime.utcnow().isoformat()
    
    try:
        # Execute kernel - no logging of trade details
        status = execute_kernel(trade_data)
        
        return AssessmentResult(
            trade_id=trade_data.trade_id,
            status=status,
            timestamp=timestamp,
            error=None
        )
        
    except Exception as e:
        # Generic error - never expose kernel details
        return AssessmentResult(
            trade_id=trade_data.trade_id,
            status="rejected",
            timestamp=timestamp,
            error="Assessment could not be completed"
        )


@app.post("/batch-assess")
async def assess_batch(
    trades: list[TradeData],
    api_key: str = Depends(verify_api_key)
):
    """
    Assess multiple trades in batch.
    
    **Limits**:
    - Maximum 100 trades per request
    - Same protection level as single assessment
    """
    # Enforce batch size limit
    if not trades:
        raise HTTPException(status_code=400, detail="Batch cannot be empty")
    
    if len(trades) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size exceeds maximum of {MAX_BATCH_SIZE} trades"
        )
    
    results = []
    for trade in trades:
        result = await assess_trade(trade, api_key)
        results.append(result)
    
    return {
        "total": len(results),
        "assessments": results,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/")
async def root():
    """API documentation"""
    return {
        "message": "Trade Assessment API",
        "documentation": "/docs",
        "endpoints": {
            "health": "GET /health",
            "assess": "POST /assess",
            "batch_assess": "POST /batch-assess"
        },
        "auth": "Include X-API-Key header in all requests"
    }


# ============================================================================
# GLOBAL EXCEPTION HANDLERS
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors - never expose internal details"""
    logger.warning("Validation error in request")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Invalid request data",
            "error": "Request validation failed"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected errors - generic response"""
    logger.error(f"Unexpected error: {type(exc).__name__}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": "An unexpected error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
