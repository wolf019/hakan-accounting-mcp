#!/usr/bin/env python3
"""
TOTP Setup Script for Kaare Accounting System
This script generates TOTP secrets and QR codes for Google Authenticator setup
"""

import json
import pyotp
import qrcode
import secrets
import sys
from pathlib import Path
from typing import List
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.database.base import DatabaseManager
from src.modules.security.totp_service import TOTPService


def generate_secret() -> str:
    """Generate a secure TOTP secret"""
    return pyotp.random_base32(length=32)


def generate_backup_codes(count: int = 8, length: int = 8) -> List[str]:
    """Generate backup codes for emergency access"""
    codes = []
    for _ in range(count):
        code = ''.join(secrets.choice('0123456789') for _ in range(length))
        codes.append(code)
    return codes


def create_qr_code(secret: str, user_email: str, issuer: str = "Kaare Accounting") -> str:
    """Create QR code for Google Authenticator"""
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=user_email,
        issuer_name=issuer
    )
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    # Save QR code as ASCII art for terminal display
    ascii_qr = qr.make_image(fill_color="black", back_color="white")
    
    # Also save as PNG file
    output_path = Path.home() / "Desktop" / f"kaare_totp_qr_{user_email.replace('@', '_')}.png"
    ascii_qr.save(str(output_path))
    
    return totp_uri, str(output_path)


def setup_totp_for_user(user_email: str = "tkaxberg@gmail.com"):
    """Main setup function for TOTP"""
    
    print("\n" + "="*60)
    print("🔐 KAARE ACCOUNTING - TOTP SETUP")
    print("="*60)
    print(f"\nSetting up TOTP for: {user_email}")
    
    # Initialize services
    db = DatabaseManager()
    totp_service = TOTPService(db)
    
    # Generate secret and backup codes
    secret = generate_secret()
    backup_codes = generate_backup_codes()
    
    print(f"\n✅ Generated TOTP Secret: {secret}")
    print("\n📱 BACKUP CODES (Save these in a secure location!):")
    print("-" * 40)
    for i, code in enumerate(backup_codes, 1):
        print(f"  {i}. {code}")
    print("-" * 40)
    
    # Create QR code
    totp_uri, qr_path = create_qr_code(secret, user_email)
    
    print(f"\n📸 QR Code saved to: {qr_path}")
    print("\n🔗 Manual Entry URI:")
    print(f"   {totp_uri}")
    
    # Save to database
    success = totp_service.save_user_secret(
        user_id=user_email,
        secret_key=secret,
        backup_codes=backup_codes,
        issuer_name="Kaare Accounting"
    )
    
    if success:
        print("\n✅ TOTP configuration saved to database")
    else:
        print("\n❌ Failed to save TOTP configuration")
        return False
    
    # Save backup codes to file
    backup_file = Path.home() / "Desktop" / f"kaare_backup_codes_{user_email.replace('@', '_')}.txt"
    with open(backup_file, 'w') as f:
        f.write("KAARE ACCOUNTING - TOTP BACKUP CODES\n")
        f.write(f"Generated: {datetime.now().isoformat()}\n")
        f.write(f"User: {user_email}\n")
        f.write("="*50 + "\n\n")
        f.write("IMPORTANT: Store these codes in a secure location!\n")
        f.write("Each code can only be used once.\n\n")
        for i, code in enumerate(backup_codes, 1):
            f.write(f"{i}. {code}\n")
        f.write("\n" + "="*50 + "\n")
        f.write("Use these codes if you lose access to your authenticator app.\n")
    
    print(f"\n💾 Backup codes saved to: {backup_file}")
    
    print("\n" + "="*60)
    print("📱 SETUP INSTRUCTIONS:")
    print("="*60)
    print("""
1. Open Google Authenticator on your phone
2. Tap the '+' button to add a new account
3. Choose 'Scan QR code'
4. Scan the QR code saved on your Desktop
   OR manually enter:
   - Account: {}
   - Key: {}
   
5. Verify setup by entering the 6-digit code shown in the app
""".format(user_email, secret))
    
    # Test verification
    print("\n🔍 VERIFICATION TEST")
    print("-" * 40)
    test_code = input("Enter the 6-digit code from Google Authenticator: ").strip()
    
    totp = pyotp.TOTP(secret)
    if totp.verify(test_code, valid_window=1):
        print("✅ SUCCESS! TOTP is correctly configured.")
        print("\nYou can now use Google Authenticator codes for secure operations.")
    else:
        print("❌ FAILED! The code doesn't match.")
        print("Please check that your phone's time is synchronized.")
        print("Try again with a new code from the app.")
    
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    
    return True


if __name__ == "__main__":
    # Check for custom email argument
    import sys
    user_email = sys.argv[1] if len(sys.argv) > 1 else "tkaxberg@gmail.com"
    
    try:
        setup_totp_for_user(user_email)
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        sys.exit(1)