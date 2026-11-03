"""
Example client for Trade Assessment API.

This demonstrates how to interact with the Trade Assessment API from a Python client.
"""

import requests
from typing import Dict, Any


class TradeAssessmentClient:
    """Client for Trade Assessment API"""
    
    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the client.
        
        Args:
            base_url: API base URL (e.g., http://localhost:8000)
            api_key: Your authorized API key
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check if API is healthy"""
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def assess_trade(self, trade_id: str, symbol: str, quantity: float,
                     price: float, direction: str, counterparty: str = None,
                     metadata: Dict = None) -> Dict[str, Any]:
        """
        Assess a single trade.
        
        Args:
            trade_id: Unique trade identifier
            symbol: Trading pair (e.g., "EURUSD")
            quantity: Trade quantity
            price: Trade price
            direction: "BUY" or "SELL"
            counterparty: Optional counterparty identifier
            metadata: Optional additional metadata
            
        Returns:
            Assessment result with status and timestamp
        """
        payload = {
            "trade_id": trade_id,
            "symbol": symbol,
            "quantity": quantity,
            "price": price,
            "direction": direction
        }
        
        if counterparty:
            payload["counterparty"] = counterparty
        if metadata:
            payload["metadata"] = metadata
        
        response = requests.post(
            f"{self.base_url}/assess",
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def assess_batch(self, trades: list) -> Dict[str, Any]:
        """
        Assess multiple trades in batch.
        
        Args:
            trades: List of trade dictionaries
            
        Returns:
            Batch assessment results
        """
        response = requests.post(
            f"{self.base_url}/batch-assess",
            json=trades,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()


def main():
    """Example usage of the TradeAssessmentClient"""
    
    # Initialize client
    client = TradeAssessmentClient(
        base_url="http://localhost:8000",
        api_key="your-api-key-here"  # Replace with actual API key
    )
    
    print("Trade Assessment API - Client Example")
    print("=" * 60)
    
    # Test health check
    try:
        health = client.health_check()
        print(f"✅ API Health: {health['status']}")
    except Exception as e:
        print(f"❌ API Health Check Failed: {e}")
        return
    
    # Example 1: Assess a single trade
    print(f"\nAssessing single trade...")
    try:
        result = client.assess_trade(
            trade_id="TRD-001",
            symbol="EURUSD",
            quantity=1000000,
            price=1.0850,
            direction="BUY",
            counterparty="BANK-A"
        )
        
        print(f"Trade ID: {result['trade_id']}")
        print(f"Status: {result['status']}")
        print(f"Timestamp: {result['timestamp']}")
        if result.get('error'):
            print(f"Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Trade Assessment Failed: {e}")
        return
    
    # Example 2: Batch assessment
    print(f"\n\nAssessing batch of trades...")
    trades = [
        {
            "trade_id": "TRD-002",
            "symbol": "GBPUSD",
            "quantity": 500000,
            "price": 1.2750,
            "direction": "BUY"
        },
        {
            "trade_id": "TRD-003",
            "symbol": "EURUSD",
            "quantity": 2000000,
            "price": 1.0820,
            "direction": "SELL",
            "metadata": {"counterparty": "BANK-B", "urgency": "high"}
        }
    ]
    
    try:
        results = client.assess_batch(trades)
        print(f"✅ Assessed {results['total']} trades in batch")
        for assessment in results['assessments']:
            print(f"  - {assessment['trade_id']}: {assessment['status']}")
            
    except Exception as e:
        print(f"❌ Batch Assessment Failed: {e}")
        return
    
    print("\n✅ Examples completed successfully!")


if __name__ == "__main__":
    main()
