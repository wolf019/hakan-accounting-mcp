# TOTP Setup for Kaare Accounting

## 🔐 Quick Setup Guide

### 1. Initial Setup (One-time)

Run the setup script to generate your TOTP secret and backup codes:

```bash
# From project root
python src/totp_setup/setup_totp.py

# Or with custom email
python src/totp_setup/setup_totp.py your-email@example.com
```

This will:
- Generate a secure TOTP secret
- Create 8 backup codes
- Save a QR code to your Desktop
- Save backup codes to a text file on your Desktop
- Store everything securely in the database

### 2. Configure Google Authenticator

1. Open Google Authenticator on your phone
2. Tap the '+' button
3. Choose 'Scan QR code'
4. Scan the QR code from your Desktop
5. Verify by entering the 6-digit code shown in the app

### 3. Test Your Setup

```bash
# Test your TOTP codes
python src/totp_setup/verify_totp.py
```

## 📱 Using TOTP with MCP Server

Once configured, use TOTP codes directly in MCP function calls:

```python
# Example: Supersede a voucher with TOTP
supersede_voucher(
    original_voucher_id=21,
    replacement_voucher_id=22,
    reason="Balance error corrected",
    user_id="your-email@example.com",
    totp_code="123456"  # Get this from Google Authenticator
)
```

## 🆘 Emergency Access

If you lose access to Google Authenticator:

1. Use one of your 8-digit backup codes
2. Backup codes work the same as TOTP codes
3. Each backup code can only be used once
4. Store backup codes securely (not in the same place as your phone!)

Example with backup code:
```python
supersede_voucher(
    original_voucher_id=21,
    replacement_voucher_id=22,
    reason="Emergency correction",
    user_id="your-email@example.com",
    totp_code="12345678"  # 8-digit backup code
)
```

## 🔄 Re-authentication

If you need to reset or reconfigure TOTP:

```bash
# Re-run setup (will overwrite existing configuration)
python src/totp_setup/setup_totp.py
```

## ⚠️ Security Notes

1. **Backup Codes**: Save the backup codes file from your Desktop to a secure location
2. **QR Code**: Delete the QR code image from Desktop after scanning
3. **Time Sync**: Ensure your phone's time is synchronized (automatic time setting)
4. **Rate Limiting**: Max 3 attempts per 30 seconds, 15-minute lockout after 5 failures

## 🛠️ Troubleshooting

### Code Not Working?
- Check phone time synchronization
- Try the previous or next code (30-second windows)
- Use verify_totp.py to test

### Account Locked?
- Wait 15 minutes for automatic unlock
- Use a backup code if urgent

### Lost Phone?
- Use backup codes
- Re-run setup_totp.py to generate new secret

## 📋 Files Created

After setup, you'll have:
- `~/Desktop/totp_qr_your-email@example.com.png` - QR code for scanning
- `~/Desktop/backup_codes_your-email@example.com.txt` - Emergency backup codes
- Database entries with encrypted TOTP configuration

Remember to move these files to secure locations!
