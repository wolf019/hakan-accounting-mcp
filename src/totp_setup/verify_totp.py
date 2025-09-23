#!/usr/bin/env python3
"""
TOTP Verification Test Script
Use this to test your TOTP codes after setup
"""

import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.base import DatabaseManager
from src.modules.security.totp_service import TOTPService


def test_totp_verification(user_email: str = "tkaxberg@gmail.com"):
    """Test TOTP verification"""
    
    print("\n" + "="*60)
    print("🔐 TOTP VERIFICATION TEST")
    print("="*60)
    print(f"\nUser: {user_email}")
    
    # Initialize services
    db = DatabaseManager()
    totp_service = TOTPService(db)
    
    while True:
        print("\n" + "-"*40)
        print("Options:")
        print("1. Test TOTP code (6 digits)")
        print("2. Test backup code (8 digits)")
        print("3. View security audit")
        print("4. Exit")
        
        choice = input("\nChoice (1-4): ").strip()
        
        if choice == "1":
            code = input("Enter 6-digit TOTP code: ").strip()
            if len(code) != 6 or not code.isdigit():
                print("❌ Invalid format. Must be 6 digits.")
                continue
            
            result = totp_service.verify_totp_operation(
                user_id=user_email,
                totp_code=code,
                operation_type="TEST_VERIFICATION",
                ip_address="127.0.0.1",
                user_agent="Test Script"
            )
            
            if result["success"]:
                print("✅ SUCCESS! Code verified.")
                print(f"   Verified at: {result['verified_at']}")
                print(f"   Expires at: {result['expires_at']}")
            else:
                print(f"❌ FAILED: {result.get('error_message', 'Unknown error')}")
                if result.get("attempts_remaining"):
                    print(f"   Attempts remaining: {result['attempts_remaining']}")
                if result.get("retry_after"):
                    print(f"   Retry after: {result['retry_after']} seconds")
        
        elif choice == "2":
            code = input("Enter 8-digit backup code: ").strip()
            if len(code) != 8 or not code.isdigit():
                print("❌ Invalid format. Must be 8 digits.")
                continue
            
            result = totp_service.verify_totp_operation(
                user_id=user_email,
                totp_code=code,
                operation_type="TEST_BACKUP_CODE",
                ip_address="127.0.0.1",
                user_agent="Test Script"
            )
            
            if result["success"]:
                print("✅ SUCCESS! Backup code verified and consumed.")
                print("⚠️  This backup code has been used and cannot be used again.")
            else:
                print(f"❌ FAILED: {result.get('error_message', 'Invalid backup code')}")
        
        elif choice == "3":
            audit = totp_service.get_security_audit(user_email, days=7)
            print(f"\n📋 Security Audit (Last 7 days):")
            print("-" * 40)
            
            if not audit:
                print("No verification attempts found.")
            else:
                for entry in audit[:10]:  # Show last 10
                    status = "✅" if entry["success"] else "❌"
                    print(f"{status} {entry['created_at']} - {entry['operation_type']}")
                    if not entry["success"]:
                        print(f"    Failure: {entry.get('failure_reason', 'Unknown')}")
        
        elif choice == "4":
            print("\nExiting...")
            break
        
        else:
            print("Invalid choice. Please enter 1-4.")


if __name__ == "__main__":
    # Check for custom email argument
    user_email = sys.argv[1] if len(sys.argv) > 1 else "tkaxberg@gmail.com"
    
    try:
        test_totp_verification(user_email)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)