# Internal-Only Annotation Workflow Documentation

## 🔐 Security Policy: ALL Voucher Annotations Require TOTP

**CRITICAL SECURITY DIRECTIVE**: As of Version 0.2.0, ALL voucher annotations affect the audit trail and require TOTP two-factor authentication.

### Public API Restrictions

The public `add_voucher_annotation()` method has been **REMOVED** from the MCP server API. This was a critical security vulnerability that allowed bypassing TOTP protection for audit trail modifications.

### Secure Annotation Workflow

#### 1. Public MCP Tools (TOTP-Protected)
- `add_secure_voucher_annotation()` - Requires TOTP for ALL annotation types
- `supersede_voucher()` - Requires TOTP for voucher supersession
- `void_voucher()` - Requires TOTP for voucher voiding

#### 2. Internal Methods (System Use Only)
- `VoucherAnnotationService._add_internal_annotation()` - Bypasses public restrictions
- Called internally by TOTP-verified operations only
- Not exposed via MCP API

### Annotation Type Security Matrix

| Annotation Type | Public API | Internal API | TOTP Required | Use Case |
|-----------------|------------|--------------|---------------|----------|
| `NOTE` | ✅ add_secure_voucher_annotation | ✅ _add_internal_annotation | ✅ Yes | General notes |
| `CORRECTION` | ✅ add_secure_voucher_annotation | ✅ _add_internal_annotation | ✅ Yes | Error corrections |
| `REVERSAL` | ✅ add_secure_voucher_annotation | ✅ _add_internal_annotation | ✅ Yes | Transaction reversals |
| `SUPERSEDED` | ❌ BLOCKED | ✅ _add_internal_annotation | ✅ Yes | Via supersede_voucher() only |
| `VOID` | ❌ BLOCKED | ✅ _add_internal_annotation | ✅ Yes | Via void_voucher() only |
| `CREATED` | ❌ BLOCKED | ✅ _add_internal_annotation | ✅ Yes | System-generated only |

### Security Features

#### Rate Limiting
- Maximum 3 TOTP attempts per 30 seconds
- Prevents brute force attacks on TOTP codes

#### Account Lockout
- 15-minute lockout after 5 failed TOTP attempts
- Can be bypassed with backup codes

#### Backup Codes
- 8 single-use emergency codes per user
- Generated during TOTP setup
- Provide emergency access during lockout

#### Audit Trail
- Every TOTP verification logged with timestamp
- User identification and IP tracking
- Operation type and result recorded
- Complete security audit accessible via `get_voucher_history()`

### Implementation Details

#### Secure Annotation Flow
```python
# 1. User calls MCP tool
add_secure_voucher_annotation(voucher_id, "NOTE", "Message", "user@email.com", "123456")

# 2. SecureVoucherService validates TOTP
totp_result = self.totp_service.verify_totp_operation(...)

# 3. If TOTP valid, call internal method
annotation_result = self.annotation_service._add_internal_annotation(
    security_verified=True,
    totp_verification_id=totp_result["verification_id"]
)
```

#### Supersession Flow
```python
# 1. User calls supersede_voucher with TOTP
supersede_voucher(original_id, replacement_id, "reason", "user@email.com", "123456")

# 2. TOTP verified, then internal annotations created
self._add_internal_annotation(annotation_type="SUPERSEDED", ...)  # Original
self._add_internal_annotation(annotation_type="CREATED", ...)     # Replacement
```

### Error Handling

#### Common TOTP Errors
- `INVALID_TOTP`: Wrong code, check Google Authenticator
- `RATE_LIMITED`: Too many attempts, wait and retry
- `ACCOUNT_LOCKED`: Account locked, use backup code or wait 15 minutes
- `EXPIRED_CODE`: TOTP codes expire every 30 seconds

#### Security Violation Errors
- `SECURITY_RESTRICTED_TYPE`: Attempting SUPERSEDED/VOID via public API
- `MISSING_TOTP_VERIFICATION`: Internal method called without TOTP
- `INVALID_ANNOTATION_TYPE`: Unknown annotation type

### Migration from Legacy System

#### Old Insecure Pattern (REMOVED)
```python
# ❌ This no longer works - security vulnerability fixed
add_voucher_annotation(voucher_id, "SUPERSEDED", "Reason")
```

#### New Secure Pattern (REQUIRED)
```python
# ✅ All annotations require TOTP
add_secure_voucher_annotation(voucher_id, "NOTE", "Reason", "user@email.com", totp_code)

# ✅ Supersession has dedicated method
supersede_voucher(original_id, replacement_id, "Reason", "user@email.com", totp_code)
```

### Best Practices

1. **Always Use TOTP**: Never attempt to bypass security for "convenience"
2. **Document Reasons**: Be specific in annotation messages
3. **Use Correct Methods**: supersede_voucher() for replacements, not manual annotations
4. **Keep Backup Codes Safe**: Store securely, don't share
5. **Monitor Security Audit**: Regular review of TOTP verification logs

### Compliance Notes

This security model ensures:
- **Swedish Audit Requirements**: Complete trail with security verification
- **Professional Standards**: Bank-level security for financial records
- **Regulatory Compliance**: Immutable audit trail with authenticated changes
- **Internal Controls**: Segregation of duties through TOTP requirements

### Emergency Procedures

#### Account Lockout Recovery
1. Wait 15 minutes for automatic unlock
2. OR use backup code for immediate access
3. Contact system administrator if all backup codes used

#### TOTP Device Loss
1. Use remaining backup codes for immediate access
2. Run `python src/totp_setup/setup_totp.py` to regenerate
3. Set up new Google Authenticator with new QR code
4. New backup codes will be generated

### System Integration

The internal annotation workflow integrates with:
- **Financial Reporting**: superseded vouchers excluded by default
- **Trial Balance**: clean view without superseded entries
- **Security Audit**: complete TOTP verification history
- **Swedish Compliance**: proper documentation for Skatteverket

This security model represents a critical upgrade from the previous vulnerable system to bank-level security standards required for professional accounting systems.