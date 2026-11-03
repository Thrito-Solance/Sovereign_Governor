#!/usr/bin/env python3
"""
Generate secure API keys for Trade Assessment API.

Run this script to generate new API keys. Store them securely and update
your .env file with the generated keys.

Usage:
    python generate_keys.py [--count N]
    python generate_keys.py --count 5  # Generate 5 keys
"""

import secrets
import argparse
import json
from datetime import datetime


def generate_api_key(length: int = 32) -> str:
    """
    Generate a cryptographically secure API key.
    
    Args:
        length: Length of the key (default 32 characters)
        
    Returns:
        Secure random API key
    """
    return secrets.token_urlsafe(length)


def main():
    parser = argparse.ArgumentParser(
        description="Generate secure API keys for Trade Assessment API"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of keys to generate (default: 1)"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("TRADE ASSESSMENT API - KEY GENERATION")
    print("="*70 + "\n")
    
    keys = []
    for i in range(args.count):
        key = generate_api_key()
        keys.append(key)
        print(f"[{i+1}] {key}")
    
    # Format for .env file
    print("\n" + "-"*70)
    print("Add this to your .env file:")
    print("-"*70)
    print(f"AUTHORIZED_API_KEYS={','.join(keys)}\n")
    
    # Save to file
    filename = f"api_keys_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump({
            "generated": datetime.now().isoformat(),
            "count": len(keys),
            "keys": keys
        }, f, indent=2)
    
    print(f"Keys saved to: {filename}")
    print("\n⚠️  SECURITY: Keep these keys secret and handle with care!")
    print("Store them in a secure secrets manager (e.g., Azure KeyVault, AWS Secrets Manager)")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
