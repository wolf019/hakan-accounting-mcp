"""
Secure voucher operations with TOTP protection
Combines voucher annotation service with TOTP security for critical operations
"""

from typing import Dict, Optional

from ...database.base import DatabaseManager
from ..security.totp_service import TOTPService
from .voucher_annotation_service import VoucherAnnotationService


class SecureVoucherService:
    """Service for TOTP-protected voucher operations"""
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        """Initialize secure voucher service"""
        self.db = db or DatabaseManager()
        self.totp_service = TOTPService(self.db)
        self.annotation_service = VoucherAnnotationService(self.db)
    
    def supersede_voucher_with_totp(
        self,
        original_voucher_id: int,
        replacement_voucher_id: int,
        reason: str,
        user_id: str,
        totp_code: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict:
        """
        Mark voucher as superseded with TOTP security verification
        
        This is the main MCP-compatible function that combines TOTP verification
        with voucher supersession in a single atomic operation.
        
        Args:
            original_voucher_id: Voucher being replaced
            replacement_voucher_id: Correct replacement voucher
            reason: Business justification (max 200 chars)
            user_id: User performing operation
            totp_code: 6-digit TOTP from authenticator app or 8-digit backup code
            ip_address: Optional client IP for audit
            user_agent: Optional client user agent for audit
        
        Returns:
            Success with details or failure with error information
        """
        
        # Validate reason length
        if len(reason) > 200:
            return {
                "success": False,
                "error": "Reason too long (max 200 characters)",
                "reason_length": len(reason)
            }
        
        # Verify TOTP first
        totp_result = self.totp_service.verify_totp_operation(
            user_id=user_id,
            totp_code=totp_code,
            operation_type="SUPERSEDE_VOUCHER",
            voucher_id=original_voucher_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not totp_result["success"]:
            # Return TOTP error details
            return totp_result
        
        # TOTP verified, proceed with supersession
        supersede_result = self.annotation_service.supersede_voucher(
            original_voucher_id=original_voucher_id,
            replacement_voucher_id=replacement_voucher_id,
            reason=reason,
            user_id=user_id,
            totp_verification_id=totp_result["verification_id"]
        )
        
        if not supersede_result["success"]:
            return supersede_result
        
        # Combine results
        return {
            "success": True,
            "original_voucher": supersede_result["original_voucher"],
            "replacement_voucher": supersede_result["replacement_voucher"],
            "security": {
                "totp_verified": True,
                "verification_time": totp_result["verified_at"],
                "audit_log_id": totp_result["verification_id"],
                "backup_code_used": totp_result.get("backup_code_used", False)
            },
            "annotations_created": supersede_result["annotations_created"],
            "message": f"Voucher {original_voucher_id} successfully superseded by {replacement_voucher_id}"
        }
    
    def void_voucher_with_totp(
        self,
        voucher_id: int,
        reason: str,
        user_id: str,
        totp_code: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict:
        """
        Void a voucher with TOTP security verification
        
        Args:
            voucher_id: Voucher to void
            reason: Business justification
            user_id: User performing operation
            totp_code: 6-digit TOTP or 8-digit backup code
            ip_address: Optional client IP
            user_agent: Optional client user agent
        
        Returns:
            Success with details or failure with error
        """
        
        # Verify TOTP first
        totp_result = self.totp_service.verify_totp_operation(
            user_id=user_id,
            totp_code=totp_code,
            operation_type="VOID_VOUCHER",
            voucher_id=voucher_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not totp_result["success"]:
            return totp_result
        
        # TOTP verified, proceed with voiding
        void_result = self.annotation_service.void_voucher(
            voucher_id=voucher_id,
            reason=reason,
            user_id=user_id,
            totp_verification_id=totp_result["verification_id"]
        )
        
        if not void_result["success"]:
            return void_result
        
        # Combine results
        return {
            "success": True,
            "voucher_id": voucher_id,
            "status": "VOID",
            "security": {
                "totp_verified": True,
                "verification_time": totp_result["verified_at"],
                "audit_log_id": totp_result["verification_id"]
            },
            "message": f"Voucher {voucher_id} successfully voided"
        }
    
    def add_secure_annotation(
        self,
        voucher_id: int,
        annotation_type: str,
        message: str,
        user_id: str,
        totp_code: str,
        related_voucher_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict:
        """
        Add annotation to voucher with TOTP security verification
        
        ALL voucher annotations affect audit trail and require TOTP protection.
        
        Args:
            voucher_id: Target voucher ID
            annotation_type: CORRECTION | REVERSAL | NOTE (SUPERSEDED/VOID use dedicated methods)
            message: Annotation message
            user_id: User performing operation
            totp_code: 6-digit TOTP from authenticator app or 8-digit backup code
            related_voucher_id: Optional related voucher
            ip_address: Optional client IP for audit
            user_agent: Optional client user agent for audit
        
        Returns:
            Success/failure status with TOTP verification details
        """
        
        # Verify TOTP first
        totp_result = self.totp_service.verify_totp_operation(
            user_id=user_id,
            totp_code=totp_code,
            operation_type="ADD_ANNOTATION",
            voucher_id=voucher_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if not totp_result["success"]:
            return totp_result
        
        # TOTP verified, add annotation using internal method
        annotation_result = self.annotation_service._add_internal_annotation(
            voucher_id=voucher_id,
            annotation_type=annotation_type,
            message=message,
            related_voucher_id=related_voucher_id,
            created_by=user_id,
            security_verified=True,
            totp_verification_id=totp_result["verification_id"]
        )
        
        if not annotation_result["success"]:
            return annotation_result
        
        return {
            "success": True,
            "annotation_id": annotation_result["annotation_id"],
            "voucher_id": voucher_id,
            "annotation_type": annotation_type,
            "security": {
                "totp_verified": True,
                "verification_time": totp_result["verified_at"],
                "audit_log_id": totp_result["verification_id"]
            },
            "message": f"Secure annotation added to voucher {voucher_id}"
        }
    
    def get_voucher_history(self, voucher_id: int) -> Dict:
        """
        Get complete voucher history including security audit
        
        Args:
            voucher_id: Voucher to analyze
        
        Returns:
            Complete history with annotations and security audit
        """
        
        return self.annotation_service.get_voucher_history(voucher_id)
    
    def get_user_security_audit(self, user_id: str, days: int = 30) -> Dict:
        """
        Get security audit log for a user
        
        Args:
            user_id: User to audit
            days: Number of days to look back
        
        Returns:
            Security audit entries
        """
        
        audit_entries = self.totp_service.get_security_audit(user_id, days)
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_verifications": len(audit_entries),
            "successful_verifications": sum(1 for e in audit_entries if e.get("success")),
            "failed_attempts": sum(1 for e in audit_entries if not e.get("success")),
            "entries": audit_entries
        }