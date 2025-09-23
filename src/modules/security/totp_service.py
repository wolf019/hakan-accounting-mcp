import hashlib
import json
import pyotp
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from ...database.base import DatabaseManager


class TOTPService:
    """TOTP (Time-based One-Time Password) service for secure voucher operations"""
    
    TOTP_CONFIG = {
        "issuer_name": "Kaare Accounting",
        "digits": 6,
        "interval": 30,
        "algorithm": "sha1",
        "window": 1,  # Accept ±30s time drift
        "secret_length": 32,
        
        # Security Controls
        "rate_limit": {
            "max_attempts": 3,  # Per 30-second window
            "lockout_threshold": 5,  # Failed attempts before lockout
            "lockout_duration": 900,  # 15 minutes in seconds
            "cleanup_interval": 3600  # Clear old rate limit data
        },
        
        # Backup Codes
        "backup_codes": {
            "count": 8,
            "length": 8,
            "use_once": True
        }
    }
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        """Initialize TOTP service with database connection"""
        self.db = db or DatabaseManager()
    
    def verify_totp_operation(
        self,
        user_id: str,
        totp_code: str,
        operation_type: str,
        voucher_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict:
        """
        Core TOTP verification for sensitive operations with rate limiting
        
        Args:
            user_id: User performing the operation
            totp_code: 6-digit TOTP code or 8-digit backup code
            operation_type: 'SUPERSEDE_VOUCHER', 'VOID_VOUCHER', etc.
            voucher_id: Optional voucher being operated on
            ip_address: Client IP for audit logging
            user_agent: Client user agent for audit logging
        
        Returns:
            Success: {"success": True, "verification_id": 123, ...}
            Failure: {"success": False, "error_code": "...", ...}
        """
        
        # Check rate limiting first
        rate_limit_check = self._check_rate_limit(user_id)
        if not rate_limit_check["allowed"]:
            return rate_limit_check
        
        # Get user's TOTP secret
        user_secret = self._get_user_secret(user_id)
        if not user_secret:
            return {
                "success": False,
                "error_code": "NO_TOTP_CONFIGURED",
                "error_message": "TOTP not configured for this user",
                "help": "Please configure TOTP using the setup script"
            }
        
        # Check if account is locked
        if user_secret.get("locked_until"):
            locked_until = datetime.fromisoformat(user_secret["locked_until"])
            if datetime.now() < locked_until:
                return {
                    "success": False,
                    "error_code": "ACCOUNT_LOCKED",
                    "error_message": "Account locked due to repeated failures",
                    "unlock_time": locked_until.isoformat(),
                    "emergency_options": ["Use backup code", "Contact administrator"]
                }
        
        # Verify the TOTP code
        verification_result = False
        is_backup_code = False
        
        if len(totp_code) == 6:
            # Standard TOTP verification
            totp = pyotp.TOTP(
                user_secret["secret_key"],
                digits=self.TOTP_CONFIG["digits"],
                interval=self.TOTP_CONFIG["interval"]
            )
            verification_result = totp.verify(
                totp_code,
                valid_window=self.TOTP_CONFIG["window"]
            )
        elif len(totp_code) == 8:
            # Backup code verification
            is_backup_code = True
            verification_result = self._verify_backup_code(user_id, totp_code)
        
        # Log the verification attempt
        verification_id = self._log_verification(
            user_id=user_id,
            operation_type=operation_type,
            voucher_id=voucher_id,
            totp_code_hash=hashlib.sha256(totp_code.encode()).hexdigest(),
            success=verification_result,
            failure_reason=None if verification_result else "INVALID_CODE",
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Update rate limiting based on result
        self._update_rate_limit(user_id, verification_result)
        
        if verification_result:
            # Update last used timestamp
            self._update_last_used(user_id)
            
            return {
                "success": True,
                "verification_id": verification_id,
                "user_id": user_id,
                "operation_type": operation_type,
                "verified_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(seconds=30)).isoformat(),
                "backup_code_used": is_backup_code
            }
        else:
            # Get remaining attempts
            attempts_info = self._get_attempts_info(user_id)
            
            return {
                "success": False,
                "error_code": "TOTP_INVALID",
                "error_message": "Invalid TOTP code provided",
                "retry_allowed": attempts_info["retry_allowed"],
                "attempts_remaining": attempts_info["attempts_remaining"],
                "security_note": f"Account will be locked after {attempts_info['lockout_warning']} more failed attempts",
                "help": "Ensure authenticator app time is synchronized"
            }
    
    def _check_rate_limit(self, user_id: str) -> Dict:
        """Check if user is rate limited"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM totp_rate_limits WHERE user_id = ?",
                (user_id,)
            )
            rate_limit = cursor.fetchone()
            
            if not rate_limit:
                # No rate limit record, allow
                return {"allowed": True}
            
            # Check if account is locked
            if rate_limit["locked_until"]:
                locked_until = datetime.fromisoformat(rate_limit["locked_until"])
                if datetime.now() < locked_until:
                    retry_after = int((locked_until - datetime.now()).total_seconds())
                    return {
                        "allowed": False,
                        "success": False,
                        "error_code": "RATE_LIMITED",
                        "error_message": "Too many TOTP attempts",
                        "retry_after": retry_after,
                        "lockout_warning": f"Account locked for {retry_after} seconds"
                    }
            
            # Check current window attempts
            if rate_limit["window_start"]:
                window_start = datetime.fromisoformat(rate_limit["window_start"])
                window_elapsed = (datetime.now() - window_start).total_seconds()
                
                if window_elapsed < 30:  # Still in same 30-second window
                    if rate_limit["attempts"] >= self.TOTP_CONFIG["rate_limit"]["max_attempts"]:
                        retry_after = int(30 - window_elapsed)
                        return {
                            "allowed": False,
                            "success": False,
                            "error_code": "RATE_LIMITED",
                            "error_message": "Too many attempts in current window",
                            "retry_after": retry_after,
                            "lockout_warning": f"{self.TOTP_CONFIG['rate_limit']['lockout_threshold'] - rate_limit['total_failures']} more failures will lock account"
                        }
            
            return {"allowed": True}
    
    def _get_user_secret(self, user_id: str) -> Optional[Dict]:
        """Get user's TOTP secret and configuration"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM user_totp_secrets WHERE user_id = ? AND is_active = 1",
                (user_id,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def _verify_backup_code(self, user_id: str, code: str) -> bool:
        """Verify and consume a backup code"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT backup_codes FROM user_totp_secrets WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            
            if not row or not row["backup_codes"]:
                return False
            
            backup_codes = json.loads(row["backup_codes"])
            
            # Check if code is valid
            if code in backup_codes:
                # Remove used code
                backup_codes.remove(code)
                
                # Update backup codes
                cursor.execute(
                    "UPDATE user_totp_secrets SET backup_codes = ? WHERE user_id = ?",
                    (json.dumps(backup_codes), user_id)
                )
                conn.commit()
                return True
            
            return False
    
    def _log_verification(
        self,
        user_id: str,
        operation_type: str,
        voucher_id: Optional[int],
        totp_code_hash: str,
        success: bool,
        failure_reason: Optional[str],
        ip_address: Optional[str],
        user_agent: Optional[str]
    ) -> int:
        """Log TOTP verification attempt"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO totp_verification_log (
                    user_id, operation_type, voucher_id, totp_code_hash,
                    success, failure_reason, ip_address, user_agent
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, operation_type, voucher_id, totp_code_hash,
                success, failure_reason, ip_address, user_agent
            ))
            conn.commit()
            return cursor.lastrowid or 0
    
    def _update_rate_limit(self, user_id: str, success: bool):
        """Update rate limiting counters"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get current rate limit
            cursor.execute(
                "SELECT * FROM totp_rate_limits WHERE user_id = ?",
                (user_id,)
            )
            rate_limit = cursor.fetchone()
            
            now = datetime.now()
            
            if not rate_limit:
                # Create new rate limit record
                cursor.execute("""
                    INSERT INTO totp_rate_limits (
                        user_id, attempts, window_start, total_failures
                    ) VALUES (?, ?, ?, ?)
                """, (
                    user_id,
                    1 if not success else 0,
                    now.isoformat(),
                    1 if not success else 0
                ))
            else:
                window_start = datetime.fromisoformat(rate_limit["window_start"]) if rate_limit["window_start"] else now
                window_elapsed = (now - window_start).total_seconds()
                
                if window_elapsed >= 30:
                    # New window
                    attempts = 1 if not success else 0
                    window_start = now
                else:
                    # Same window
                    attempts = rate_limit["attempts"] + (1 if not success else 0)
                
                total_failures = rate_limit["total_failures"] + (1 if not success else 0)
                
                # Check for lockout
                locked_until = None
                if total_failures >= self.TOTP_CONFIG["rate_limit"]["lockout_threshold"]:
                    locked_until = (now + timedelta(seconds=self.TOTP_CONFIG["rate_limit"]["lockout_duration"])).isoformat()
                
                # Reset on success
                if success:
                    total_failures = 0
                    attempts = 0
                
                cursor.execute("""
                    UPDATE totp_rate_limits
                    SET attempts = ?, window_start = ?, total_failures = ?, locked_until = ?
                    WHERE user_id = ?
                """, (
                    attempts, window_start.isoformat(), total_failures, locked_until, user_id
                ))
            
            conn.commit()
    
    def _update_last_used(self, user_id: str):
        """Update last used timestamp for TOTP"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE user_totp_secrets SET last_used_at = ? WHERE user_id = ?",
                (datetime.now().isoformat(), user_id)
            )
            conn.commit()
    
    def _get_attempts_info(self, user_id: str) -> Dict:
        """Get information about remaining attempts"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM totp_rate_limits WHERE user_id = ?",
                (user_id,)
            )
            rate_limit = cursor.fetchone()
            
            if not rate_limit:
                return {
                    "retry_allowed": True,
                    "attempts_remaining": self.TOTP_CONFIG["rate_limit"]["max_attempts"],
                    "lockout_warning": self.TOTP_CONFIG["rate_limit"]["lockout_threshold"]
                }
            
            window_start = datetime.fromisoformat(rate_limit["window_start"]) if rate_limit["window_start"] else datetime.now()
            window_elapsed = (datetime.now() - window_start).total_seconds()
            
            if window_elapsed >= 30:
                # New window
                attempts_remaining = self.TOTP_CONFIG["rate_limit"]["max_attempts"]
            else:
                attempts_remaining = max(0, self.TOTP_CONFIG["rate_limit"]["max_attempts"] - rate_limit["attempts"])
            
            lockout_warning = self.TOTP_CONFIG["rate_limit"]["lockout_threshold"] - rate_limit["total_failures"]
            
            return {
                "retry_allowed": attempts_remaining > 0,
                "attempts_remaining": attempts_remaining,
                "lockout_warning": max(0, lockout_warning)
            }
    
    def generate_backup_codes(self, count: int = 8, length: int = 8) -> List[str]:
        """Generate backup codes for emergency access"""
        codes = []
        for _ in range(count):
            code = ''.join(secrets.choice('0123456789') for _ in range(length))
            codes.append(code)
        return codes
    
    def save_user_secret(
        self,
        user_id: str,
        secret_key: str,
        backup_codes: List[str],
        issuer_name: str = "Kaare Accounting"
    ) -> bool:
        """Save user's TOTP secret and backup codes"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user already has a secret
            cursor.execute(
                "SELECT id FROM user_totp_secrets WHERE user_id = ?",
                (user_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing
                cursor.execute("""
                    UPDATE user_totp_secrets
                    SET secret_key = ?, backup_codes = ?, issuer_name = ?, is_active = 1
                    WHERE user_id = ?
                """, (
                    secret_key, json.dumps(backup_codes), issuer_name, user_id
                ))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO user_totp_secrets (
                        user_id, secret_key, backup_codes, issuer_name
                    ) VALUES (?, ?, ?, ?)
                """, (
                    user_id, secret_key, json.dumps(backup_codes), issuer_name
                ))
            
            conn.commit()
            return True
    
    def get_security_audit(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get security audit log for user"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            since_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            cursor.execute("""
                SELECT * FROM totp_verification_log
                WHERE user_id = ? AND created_at >= ?
                ORDER BY created_at DESC
            """, (user_id, since_date))
            
            return [dict(row) for row in cursor.fetchall()]