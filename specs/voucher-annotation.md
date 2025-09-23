# Enhanced MCP Accounting Server - TOTP & Voucher Annotation System
**Version:** 2.0
**Project:** MCP Accounting Server Enhancement
**Priority:** High (Security Critical)
**Compliance:** Swedish Accounting Standards (BAS 2022) + RFC 6238 (TOTP)

## 1. Executive Summary

This specification enhances the MCP Accounting Server with professional voucher error handling and bank-level security through TOTP (Time-based One-Time Password) authentication. The system addresses the critical gap in handling erroneous vouchers while maintaining complete audit trails required by Swedish accounting standards.

### Key Improvements
- **Voucher Annotation System**: Professional error documentation with cross-references
- **TOTP Security**: RFC 6238 compliant two-factor authentication for sensitive operations
- **MCP Integration**: Seamless integration with existing MCP tool constraints
- **Audit Compliance**: Complete transaction history with security logging

## 2. Problem Statement & Business Case

### Current Issues
1. **Sequential Voucher Gaps**: Failed vouchers (e.g., ID 21) create unexplained gaps in audit trail
2. **No Error Documentation**: No way to explain why certain vouchers exist but aren't posted
3. **Security Vulnerability**: Critical voucher operations lack proper authentication
4. **Compliance Risk**: Swedish accounting law requires complete, explainable transaction histories

### Business Impact
- **Audit Complications**: 20-30 additional hours per annual review explaining gaps
- **Compliance Risk**: Potential regulatory violations for incomplete audit trails
- **Security Exposure**: Unauthorized voucher modifications possible
- **Professional Image**: Inconsistent numbering appears unprofessional to clients/auditors

## 3. Technical Architecture

### 3.1 Database Schema Enhancements

#### New Table: `voucher_annotations`
```sql
CREATE TABLE voucher_annotations (
    id SERIAL PRIMARY KEY,
    voucher_id INTEGER NOT NULL REFERENCES vouchers(id),
    annotation_type VARCHAR(20) NOT NULL CHECK (annotation_type IN
        ('SUPERSEDED', 'CORRECTION', 'REVERSAL', 'NOTE', 'VOID', 'CREATED')),
    message TEXT NOT NULL,
    related_voucher_id INTEGER REFERENCES vouchers(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255),
    security_verified BOOLEAN DEFAULT FALSE,
    totp_verification_id INTEGER REFERENCES totp_verification_log(id)
);
```

#### New Table: `user_totp_secrets`
```sql
CREATE TABLE user_totp_secrets (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL UNIQUE,
    secret_key VARCHAR(64) NOT NULL, -- Base32 encoded TOTP secret
    issuer_name VARCHAR(100) DEFAULT 'Kaare Accounting',
    is_active BOOLEAN DEFAULT TRUE,
    backup_codes TEXT[], -- JSON array of one-time backup codes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used_at TIMESTAMP,
    failed_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP
);
```

#### New Table: `totp_verification_log`
```sql
CREATE TABLE totp_verification_log (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    operation_type VARCHAR(50) NOT NULL, -- 'SUPERSEDE_VOUCHER', 'VOID_VOUCHER', etc.
    voucher_id INTEGER,
    totp_code_hash VARCHAR(128) NOT NULL, -- Hashed for security
    success BOOLEAN NOT NULL,
    failure_reason VARCHAR(100), -- 'INVALID_CODE', 'RATE_LIMITED', 'EXPIRED'
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Enhanced Table: `vouchers`
```sql
-- Add new status management columns
ALTER TABLE vouchers ADD COLUMN status VARCHAR(20) DEFAULT 'ACTIVE'
    CHECK (status IN ('ACTIVE', 'SUPERSEDED', 'VOID', 'DRAFT'));
ALTER TABLE vouchers ADD COLUMN superseded_by INTEGER REFERENCES vouchers(id);
ALTER TABLE vouchers ADD COLUMN security_level VARCHAR(20) DEFAULT 'STANDARD'
    CHECK (security_level IN ('STANDARD', 'TOTP_REQUIRED'));
```

### 3.2 TOTP Security Implementation

#### Core Configuration
```python
TOTP_CONFIG = {
    "issuer_name": "Kaare Accounting",
    "digits": 6,                    # RFC 6238 standard
    "interval": 30,                 # 30-second time windows
    "algorithm": "sha1",            # RFC 6238 compliant
    "window": 1,                    # Accept ±30s time drift
    "secret_length": 32,            # 256-bit entropy

    # Security Controls
    "rate_limit": {
        "max_attempts": 3,          # Per 30-second window
        "lockout_threshold": 5,     # Failed attempts before lockout
        "lockout_duration": 900,    # 15 minutes
        "cleanup_interval": 3600    # Clear old rate limit data
    },

    # Backup Codes
    "backup_codes": {
        "count": 8,                 # Generated per user
        "length": 8,                # 8-digit codes
        "use_once": True           # Single-use only
    }
}
```

## 4. MCP Tool Functions

### 4.1 TOTP Management Functions

#### `verify_totp_operation` *(Core Verification Function)*
```python
def verify_totp_operation(
    user_id: str,
    totp_code: str,
    operation_type: str,
    voucher_id: Optional[int] = None
) -> dict:
    """
    Core TOTP verification for sensitive operations.

    Args:
        user_id: User performing the operation
        totp_code: 6-digit TOTP code or 8-digit backup code
        operation_type: 'SUPERSEDE_VOUCHER', 'VOID_VOUCHER', etc.
        voucher_id: Optional voucher being operated on

    Returns:
        {
            "success": True,
            "verification_id": 123,
            "user_id": "tkaxberg@gmail.com",
            "operation_type": "SUPERSEDE_VOUCHER",
            "verified_at": "2025-08-04T10:15:30Z",
            "expires_at": "2025-08-04T10:16:00Z"  # 30-second operation window
        }

    Security Features:
        - Rate limiting: Max 3 attempts per 30-second window
        - Account lockout: 15 minutes after 5 failed attempts
        - Replay protection: Each code can only be used once
        - Audit logging: All attempts logged with IP/user agent
        - Time window: Accepts codes from current + previous 30s window
        - Backup codes: Accepts 8-digit backup codes as alternative

    Usage:
        # Standard TOTP code
        verify_result = verify_totp_operation("tkaxberg@gmail.com", "123456", "SUPERSEDE_VOUCHER", 21)

        # Backup code (emergency)
        verify_result = verify_totp_operation("tkaxberg@gmail.com", "12345678", "SUPERSEDE_VOUCHER", 21)
    """
```

**Note**: TOTP setup (`generate_totp_secret`, `verify_totp_setup`) will be handled during development phase between Claude Code and Tom Axberg. MCP tools focus on operational verification only.

### 4.2 Enhanced Voucher Management

#### `add_voucher_annotation`
```python
def add_voucher_annotation(
    voucher_id: int,
    annotation_type: str,
    message: str,
    related_voucher_id: Optional[int] = None,
    created_by: str = "system"
) -> dict:
    """
    Add explanatory annotation to voucher for audit trail.

    Args:
        voucher_id: Target voucher ID
        annotation_type: SUPERSEDED | CORRECTION | REVERSAL | NOTE | VOID | CREATED
        message: Human-readable explanation (max 500 chars)
        related_voucher_id: Optional link to related voucher
        created_by: User or system creating annotation

    Returns:
        {
            "success": True,
            "annotation_id": 123,
            "message": "Annotation added successfully",
            "voucher_id": 21,
            "annotation_type": "SUPERSEDED"
        }

    Example:
        add_voucher_annotation(
            voucher_id=21,
            annotation_type="SUPERSEDED",
            message="Posting failed due to unbalanced entries. Corrected in voucher 22.",
            related_voucher_id=22,
            created_by="tkaxberg@gmail.com"
        )
    """
```

#### `supersede_voucher` *(TOTP Protected)*
```python
def supersede_voucher(
    original_voucher_id: int,
    replacement_voucher_id: int,
    reason: str,
    user_id: str,
    totp_code: str
) -> dict:
    """
    Mark voucher as superseded with TOTP security verification.

    **MCP CRITICAL**: TOTP code must be provided in function call.
    No interactive prompts possible in MCP environment.

    Args:
        original_voucher_id: Voucher being replaced
        replacement_voucher_id: Correct replacement voucher
        reason: Business justification (max 200 chars)
        user_id: User performing operation
        totp_code: 6-digit TOTP from authenticator app

    Returns:
        {
            "success": True,
            "original_voucher": {"id": 21, "status": "SUPERSEDED"},
            "replacement_voucher": {"id": 22, "status": "ACTIVE"},
            "security": {
                "totp_verified": True,
                "verification_time": "2025-08-04T10:15:30Z",
                "audit_log_id": 456
            },
            "annotations_created": 2
        }

    Security Flow:
        1. Validate TOTP code against user's secret
        2. Check rate limits and account lockout status
        3. Log verification attempt with full audit trail
        4. If verified: mark original as SUPERSEDED, add annotations
        5. Update trial balance filters to exclude superseded voucher

    Usage:
        # Get current TOTP code from authenticator app: 123456
        supersede_voucher(21, 22, "Technical posting error", "tkaxberg@gmail.com", "123456")

    Error Handling:
        - Invalid TOTP: {"success": False, "error": "INVALID_TOTP_CODE"}
        - Rate limited: {"success": False, "error": "RATE_LIMITED", "retry_after": 25}
        - Account locked: {"success": False, "error": "ACCOUNT_LOCKED", "unlock_time": "..."}
    """
```

#### `get_voucher_history`
```python
def get_voucher_history(voucher_id: int) -> dict:
    """
    Get complete history, relationships, and security audit for voucher.

    Args:
        voucher_id: Voucher to analyze

    Returns:
        {
            "voucher": {
                "id": 21,
                "description": "Betalning från Intersolia...",
                "status": "SUPERSEDED",
                "created_at": "2025-08-04T10:15:23Z",
                "total_amount": 15625.0
            },
            "relationships": {
                "superseded_by": {"id": 22, "created_at": "..."},
                "supersedes": null,
                "related_vouchers": [22]
            },
            "annotations": [
                {
                    "id": 45,
                    "type": "SUPERSEDED",
                    "message": "Posting failed...",
                    "created_by": "tkaxberg@gmail.com",
                    "created_at": "2025-08-04T10:18:45Z",
                    "security_verified": True
                }
            ],
            "security_audit": [
                {
                    "operation": "SUPERSEDE_VOUCHER",
                    "user": "tkaxberg@gmail.com",
                    "totp_verified": True,
                    "timestamp": "2025-08-04T10:18:45Z"
                }
            ]
        }

    Usage:
        # Investigate voucher 21's complete history
        history = get_voucher_history(21)
    """
```

### 4.3 Enhanced Reporting Functions

#### Modified `generate_trial_balance`
```python
def generate_trial_balance(
    include_superseded: bool = False,
    security_audit: bool = False
) -> dict:
    """
    Generate trial balance with superseded voucher filtering.

    Args:
        include_superseded: Include SUPERSEDED/VOID vouchers (default: False)
        security_audit: Include security verification details (default: False)

    Returns:
        Standard trial balance format with additional metadata:
        {
            "accounts": [...],
            "totals": {"debit": 18412.84, "credit": 18412.84},
            "balanced": True,
            "metadata": {
                "total_vouchers": 15,
                "active_vouchers": 13,
                "superseded_vouchers": 2,
                "security_protected_operations": 1
            }
        }

    Default Behavior:
        - Excludes SUPERSEDED and VOID vouchers from calculations
        - Shows clean, audit-ready trial balance
        - Includes security metadata when requested

    Usage:
        # Standard trial balance (excludes superseded)
        trial_balance = generate_trial_balance()

        # Full audit view (includes all vouchers)
        full_audit = generate_trial_balance(include_superseded=True, security_audit=True)
    """
```

## 5. MCP Integration Requirements

### 5.1 Critical MCP Constraints

#### No Interactive Input Capability
```python
# ❌ CANNOT DO: Interactive prompts in MCP tools
def supersede_voucher(...):
    totp_code = input("Enter TOTP code: ")  # IMPOSSIBLE in MCP

# ✅ CORRECT: All parameters in function call
def supersede_voucher(original_id, replacement_id, reason, user_id, totp_code):
    # totp_code provided upfront - no prompts needed
```

#### Simplified Workflow
```
Traditional Workflow:
1. User calls supersede_voucher(21, 22, "reason", "user")
2. System prompts: "Enter TOTP code:"
3. User types: 123456
4. System verifies and proceeds

MCP Workflow:
1. User opens authenticator app → sees: 123456
2. User calls: supersede_voucher(21, 22, "reason", "user", "123456")
3. System verifies immediately and proceeds
```

### 5.2 Enhanced `tools_documentation` Output

The `tools_documentation` function now includes streamlined TOTP workflow guidance:

```markdown
## 🔐 TOTP-Protected Operations

**Prerequisites**: TOTP must be configured during system setup (handled by Claude Code development process)

### Using TOTP-Protected Functions

**Workflow**:
1. Open your configured Google Authenticator app
2. Note current 6-digit code (e.g., 123456)
3. Call function immediately: `supersede_voucher(21, 22, "reason", "user@email.com", "123456")`

**Security Features**:
- ⏱️ **Rate Limited**: Max 3 attempts per 30 seconds
- 🔒 **Account Lockout**: 15 minutes after 5 failed attempts
- 🛡️ **Replay Protection**: Each code can only be used once
- 📱 **Backup Codes**: Emergency access when authenticator app unavailable
- 📋 **Full Audit**: All attempts logged with timestamp and security details

**Emergency Access**:
If authenticator app unavailable, use 8-digit backup codes:
`supersede_voucher(21, 22, "reason", "user@email.com", "12345678")`

**Setup Note**: TOTP configuration and backup codes are provided during system setup phase.
```

## 6. Professional Workflows

### 6.1 Error Correction Workflow

```
Scenario: Voucher 21 failed to post due to balance error

Step 1: Create Correct Voucher
→ create_voucher("Corrected Intersolia payment", ...)  # Returns ID: 22
→ add_journal_entry(22, "1930", debit_amount=15625, ...)
→ add_journal_entry(22, "1510", credit_amount=15625, ...)
→ post_voucher(22)  # Success

Step 2: Annotate Failed Voucher
→ add_voucher_annotation(21, "SUPERSEDED", "Balance error corrected", 22)

Step 3: Secure Supersession (TOTP Required)
→ [User opens authenticator app: 654321]
→ supersede_voucher(21, 22, "Technical posting error", "tkaxberg@gmail.com", "654321")

Result: Clean audit trail with security verification
```

### 6.2 Monthly Closing Workflow

```
Standard Month-End Process with Enhanced Security:

1. **Review All Vouchers**
   → get_voucher_history(voucher_id) for any questionable entries

2. **Generate Clean Reports**
   → generate_trial_balance()  # Excludes superseded automatically
   → generate_income_statement(start_date, end_date)

3. **Security Audit Review**
   → generate_trial_balance(security_audit=True)  # Shows TOTP operations

4. **Full Audit Documentation** (if needed)
   → generate_trial_balance(include_superseded=True)  # Complete history
```

## 7. Security & Compliance

### 7.1 Swedish Accounting Compliance (BAS 2022)
- ✅ **Complete Transaction History**: All vouchers preserved with explanations
- ✅ **Sequential Numbering**: Clear handling of gaps with annotations
- ✅ **Audit Trail Requirements**: Full documentation of corrections
- ✅ **Professional Standards**: Bank-level security for financial corrections
- ✅ **Regulatory Transparency**: Clear reasoning for all voucher changes

### 7.2 TOTP Security Standards (RFC 6238)
- ✅ **Time Synchronization**: 30-second windows with ±30s drift tolerance
- ✅ **Cryptographic Security**: SHA-1 HMAC with 256-bit secrets
- ✅ **Replay Attack Prevention**: Hash-based code usage tracking
- ✅ **Rate Limiting**: 3 attempts per 30 seconds, 15-minute lockouts
- ✅ **Backup Recovery**: 8 single-use backup codes per user
- ✅ **Comprehensive Logging**: Full audit trail of all security events

### 7.3 Enhanced Error Handling

```python
# Comprehensive error responses for all failure modes
{
    "success": False,
    "error_code": "TOTP_INVALID",
    "error_message": "Invalid TOTP code provided",
    "retry_allowed": True,
    "attempts_remaining": 2,
    "security_note": "Account will be locked after 5 failed attempts",
    "help": "Ensure authenticator app time is synchronized"
}

{
    "success": False,
    "error_code": "RATE_LIMITED",
    "error_message": "Too many TOTP attempts",
    "retry_after": 25,  # seconds
    "lockout_warning": "2 more failures will lock account for 15 minutes"
}

{
    "success": False,
    "error_code": "ACCOUNT_LOCKED",
    "error_message": "Account locked due to repeated failures",
    "unlock_time": "2025-08-04T10:30:45Z",
    "emergency_options": ["Use backup code", "Contact administrator"]
}
```

## 8. Implementation Plan & Stakeholder Requirements

### Development Team Responsibilities
- Database schema implementation and migration scripts
- PyOTP integration with secure secret generation
- QR code generation for authenticator app setup
- TOTP verification with rate limiting and security logging
- Voucher annotation system with cross-referencing
- Enhanced reporting functions with superseded voucher filtering
- Comprehensive error handling and user guidance
- MCP workflow optimization and testing

### Client Requirements & Integration Support

**Tom Axberg (Kaare Consulting) - Required Actions:**

1. **TOTP Testing & Validation**
   - Test Google Authenticator QR code scanning process
   - Validate TOTP code generation and timing
   - Test backup code functionality for emergency access
   - Verify rate limiting and account lockout behavior

2. **Business Workflow Validation**
   - Test supersede voucher workflow with real accounting scenarios
   - Validate annotation system meets audit trail requirements
   - Confirm trial balance filtering works correctly for Swedish compliance
   - Review security audit logs for completeness

3. **User Experience Feedback**
   - Evaluate TOTP setup process for ease of use
   - Test error messages for clarity and actionability
   - Confirm MCP workflow integration feels natural
   - Validate emergency procedures work as expected

### Developer Communication Protocol

**Development Environment**: Claude Code integration with direct collaboration

**Setup & Configuration Phase**:
- TOTP secret generation and QR code setup will be handled collaboratively between Claude Code and Tom Axberg during development
- Claude Code will provide direct links and setup instructions
- Database initialization and TOTP secret management handled outside MCP environment
- Google Authenticator app configuration and backup code generation managed during dev phase

**Production MCP Integration**:
- MCP tools assume TOTP is already configured and active
- Focus on operational verification and voucher management functions
- All setup complexity abstracted away from end-user MCP experience

**Developer Contact Protocol**:
Claude Code development process will naturally involve Tom Axberg for:
- **Google Authenticator Setup**: Direct setup links, QR code generation, app configuration guidance
- **Swedish Accounting Compliance**: BAS 2022 validation, audit trail requirements
- **Business Workflow Testing**: Real voucher supersession scenarios, annotation system validation
- **Security Configuration**: TOTP timing, rate limits, backup code policies
- **User Experience Optimization**: Error message clarity, workflow efficiency

**Integration Approach**:
- Claude Code handles all technical setup and provides step-by-step instructions
- Tom tests and validates business requirements during development
- MCP tools receive clean, production-ready TOTP verification functions
- Setup complexity hidden from daily MCP usage

### Implementation Phases

**Phase 1: Core Infrastructure**
- Database schema and TOTP foundation
- Basic security functions with rate limiting

**Phase 2: Voucher Management**
- Annotation system and cross-referencing
- Status management for voucher lifecycle

**Phase 3: Secure Integration**
- TOTP-protected operations implementation
- Enhanced reporting with filtering

**Phase 4: Validation & Deployment**
- End-to-end testing with Tom Axberg
- Documentation finalization and deployment

## 9. Success Metrics

### Security Improvements
- **100%** of voucher corrections require TOTP verification
- **0** unauthorized voucher modifications possible
- **15-minute** maximum window for rate limit recovery
- **8** backup codes per user for emergency access

### Audit Compliance
- **100%** voucher sequence gaps explained with annotations
- **Complete** audit trail for all corrections with timestamps
- **Professional** documentation meeting Swedish BAS 2022 standards
- **Reduced** audit review time by 20-30 hours annually

### User Experience
- **2-step** setup process for TOTP (scan QR, verify)
- **30-second** maximum time to complete secure voucher operation
- **Clear** error messages with specific next-step guidance
- **Emergency** backup codes prevent lockouts

---

**Version**: 2.0
**Last Updated**: 2025-08-04
**Next Review**: After Phase 1 implementation

This enhanced specification addresses MCP tool constraints while providing enterprise-grade security for financial operations. The system ensures complete Swedish accounting compliance while protecting against unauthorized modifications through RFC 6238-compliant TOTP authentication.
