from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

from ...database.base import DatabaseManager
from ...database.accounting_db import AccountingDatabase


class AnnotationType(Enum):
    """All types of voucher annotations (internal use)"""
    SUPERSEDED = "SUPERSEDED"  # SECURITY-SENSITIVE: Only via supersede_voucher
    CORRECTION = "CORRECTION"
    REVERSAL = "REVERSAL" 
    NOTE = "NOTE"
    VOID = "VOID"            # SECURITY-SENSITIVE: Only via void_voucher
    CREATED = "CREATED"      # INTERNAL: System-generated only


class PublicAnnotationType(Enum):
    """Public annotation types allowed via add_voucher_annotation"""
    CORRECTION = "CORRECTION"
    REVERSAL = "REVERSAL"
    NOTE = "NOTE"


class VoucherAnnotationService:
    """Service for managing voucher annotations and audit trail"""
    
    def __init__(self, db: Optional[DatabaseManager] = None):
        """Initialize voucher annotation service"""
        base_db = db or DatabaseManager()
        self.db = base_db
        self.accounting_db = AccountingDatabase(base_db)
    
    def add_voucher_annotation(
        self,
        voucher_id: int,
        annotation_type: str,
        message: str,
        related_voucher_id: Optional[int] = None,
        created_by: str = "system",
        security_verified: bool = False,
        totp_verification_id: Optional[int] = None
    ) -> Dict:
        """
        Add explanatory annotation to voucher for audit trail
        
        SECURITY RESTRICTION: Only non-sensitive annotation types allowed.
        Use supersede_voucher() for SUPERSEDED annotations.
        
        Args:
            voucher_id: Target voucher ID
            annotation_type: CORRECTION | REVERSAL | NOTE (SUPERSEDED/VOID blocked for security)
            message: Human-readable explanation (max 500 chars)
            related_voucher_id: Optional link to related voucher
            created_by: User or system creating annotation
            security_verified: Whether TOTP verification was used (internal)
            totp_verification_id: ID from TOTP verification log (internal)
        
        Returns:
            Success/failure status with annotation details
        """
        
        # Security validation: Only allow public annotation types
        try:
            PublicAnnotationType(annotation_type)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid annotation type: {annotation_type}",
                "error_code": "SECURITY_RESTRICTED_TYPE",
                "valid_types": [t.value for t in PublicAnnotationType],
                "security_note": "SUPERSEDED and VOID annotations require TOTP verification via supersede_voucher() or void_voucher()"
            }
        
        # Validate message length
        if len(message) > 500:
            return {
                "success": False,
                "error": "Message too long (max 500 characters)",
                "message_length": len(message)
            }
        
        # Check if voucher exists
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM vouchers WHERE id = ?", (voucher_id,))
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": f"Voucher {voucher_id} does not exist"
                }
            
            # Check if related voucher exists (if provided)
            if related_voucher_id:
                cursor.execute("SELECT id FROM vouchers WHERE id = ?", (related_voucher_id,))
                if not cursor.fetchone():
                    return {
                        "success": False,
                        "error": f"Related voucher {related_voucher_id} does not exist"
                    }
            
            # Insert annotation
            cursor.execute("""
                INSERT INTO voucher_annotations (
                    voucher_id, annotation_type, message, related_voucher_id,
                    created_by, security_verified, totp_verification_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                voucher_id, annotation_type, message, related_voucher_id,
                created_by, security_verified, totp_verification_id
            ))
            conn.commit()
            
            annotation_id = cursor.lastrowid
            
            return {
                "success": True,
                "annotation_id": annotation_id,
                "message": "Annotation added successfully",
                "voucher_id": voucher_id,
                "annotation_type": annotation_type
            }
    
    def _add_internal_annotation(
        self,
        voucher_id: int,
        annotation_type: str,
        message: str,
        related_voucher_id: Optional[int] = None,
        created_by: str = "system",
        security_verified: bool = False,
        totp_verification_id: Optional[int] = None
    ) -> Dict:
        """
        Internal method for adding annotations - bypasses public type restrictions.
        Used by secure operations like supersede_voucher() and void_voucher().
        """
        
        # Validate with full AnnotationType (including security-sensitive types)
        try:
            AnnotationType(annotation_type)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid annotation type: {annotation_type}",
                "valid_types": [t.value for t in AnnotationType]
            }
        
        # Validate message length
        if len(message) > 500:
            return {
                "success": False,
                "error": "Message too long (max 500 characters)",
                "message_length": len(message)
            }
        
        # Check if voucher exists
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM vouchers WHERE id = ?", (voucher_id,))
            if not cursor.fetchone():
                return {
                    "success": False,
                    "error": f"Voucher {voucher_id} does not exist"
                }
            
            # Check if related voucher exists (if provided)
            if related_voucher_id:
                cursor.execute("SELECT id FROM vouchers WHERE id = ?", (related_voucher_id,))
                if not cursor.fetchone():
                    return {
                        "success": False,
                        "error": f"Related voucher {related_voucher_id} does not exist"
                    }
            
            # Insert annotation
            cursor.execute("""
                INSERT INTO voucher_annotations (
                    voucher_id, annotation_type, message, related_voucher_id,
                    created_by, security_verified, totp_verification_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                voucher_id, annotation_type, message, related_voucher_id,
                created_by, security_verified, totp_verification_id
            ))
            conn.commit()
            
            annotation_id = cursor.lastrowid
            
            return {
                "success": True,
                "annotation_id": annotation_id,
                "message": "Internal annotation added successfully",
                "voucher_id": voucher_id,
                "annotation_type": annotation_type
            }
    
    def supersede_voucher(
        self,
        original_voucher_id: int,
        replacement_voucher_id: int,
        reason: str,
        user_id: str,
        totp_verification_id: Optional[int] = None
    ) -> Dict:
        """
        Mark voucher as superseded and update relationships
        
        Args:
            original_voucher_id: Voucher being replaced
            replacement_voucher_id: Correct replacement voucher
            reason: Business justification
            user_id: User performing operation
            totp_verification_id: ID from successful TOTP verification
        
        Returns:
            Success/failure status with details
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Verify both vouchers exist
            cursor.execute(
                "SELECT id, status FROM vouchers WHERE id IN (?, ?)",
                (original_voucher_id, replacement_voucher_id)
            )
            vouchers = cursor.fetchall()
            
            if len(vouchers) != 2:
                return {
                    "success": False,
                    "error": "One or both vouchers do not exist"
                }
            
            # Update original voucher status
            cursor.execute("""
                UPDATE vouchers
                SET status = 'SUPERSEDED', superseded_by = ?
                WHERE id = ?
            """, (replacement_voucher_id, original_voucher_id))
            
            conn.commit()
            
            # Add superseded annotation to original using internal method
            self._add_internal_annotation(
                voucher_id=original_voucher_id,
                annotation_type="SUPERSEDED",
                message=f"Superseded by voucher {replacement_voucher_id}. Reason: {reason}",
                related_voucher_id=replacement_voucher_id,
                created_by=user_id,
                security_verified=totp_verification_id is not None,
                totp_verification_id=totp_verification_id
            )
            
            # Add created annotation to replacement using internal method
            self._add_internal_annotation(
                voucher_id=replacement_voucher_id,
                annotation_type="CREATED",
                message=f"Created to replace voucher {original_voucher_id}. Reason: {reason}",
                related_voucher_id=original_voucher_id,
                created_by=user_id,
                security_verified=totp_verification_id is not None,
                totp_verification_id=totp_verification_id
            )
            
            return {
                "success": True,
                "original_voucher": {
                    "id": original_voucher_id,
                    "status": "SUPERSEDED"
                },
                "replacement_voucher": {
                    "id": replacement_voucher_id,
                    "status": "ACTIVE"
                },
                "security": {
                    "totp_verified": totp_verification_id is not None,
                    "verification_time": datetime.now().isoformat(),
                    "audit_log_id": totp_verification_id
                },
                "annotations_created": 2
            }
    
    def get_voucher_history(self, voucher_id: int) -> Dict:
        """
        Get complete history, relationships, and security audit for voucher
        
        Args:
            voucher_id: Voucher to analyze
        
        Returns:
            Complete voucher history with annotations and relationships
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Get voucher details
            cursor.execute("""
                SELECT * FROM vouchers WHERE id = ?
            """, (voucher_id,))
            voucher_row = cursor.fetchone()
            
            if not voucher_row:
                return {
                    "success": False,
                    "error": f"Voucher {voucher_id} does not exist"
                }
            
            voucher = dict(voucher_row)
            
            # Get annotations
            cursor.execute("""
                SELECT * FROM voucher_annotations
                WHERE voucher_id = ?
                ORDER BY created_at DESC
            """, (voucher_id,))
            annotations = [dict(row) for row in cursor.fetchall()]
            
            # Get related vouchers
            related_voucher_ids = set()
            if voucher.get("superseded_by"):
                related_voucher_ids.add(voucher["superseded_by"])
            
            for ann in annotations:
                if ann.get("related_voucher_id"):
                    related_voucher_ids.add(ann["related_voucher_id"])
            
            # Get superseded information
            cursor.execute("""
                SELECT id FROM vouchers WHERE superseded_by = ?
            """, (voucher_id,))
            supersedes_rows = cursor.fetchall()
            supersedes = [row["id"] for row in supersedes_rows] if supersedes_rows else None
            
            # Get security audit
            cursor.execute("""
                SELECT tl.*, va.annotation_type
                FROM totp_verification_log tl
                LEFT JOIN voucher_annotations va ON va.totp_verification_id = tl.id
                WHERE tl.voucher_id = ? OR va.voucher_id = ?
                ORDER BY tl.created_at DESC
            """, (voucher_id, voucher_id))
            security_audit = [dict(row) for row in cursor.fetchall()]
            
            return {
                "voucher": {
                    "id": voucher["id"],
                    "voucher_number": voucher.get("voucher_number"),
                    "description": voucher.get("description"),
                    "status": voucher.get("status", "ACTIVE"),
                    "created_at": voucher.get("created_at"),
                    "total_amount": voucher.get("total_amount"),
                    "is_posted": voucher.get("is_posted", False)
                },
                "relationships": {
                    "superseded_by": {
                        "id": voucher.get("superseded_by"),
                        "created_at": None  # Would need additional query
                    } if voucher.get("superseded_by") else None,
                    "supersedes": supersedes,
                    "related_vouchers": list(related_voucher_ids)
                },
                "annotations": [
                    {
                        "id": ann["id"],
                        "type": ann["annotation_type"],
                        "message": ann["message"],
                        "related_voucher_id": ann.get("related_voucher_id"),
                        "created_by": ann["created_by"],
                        "created_at": ann["created_at"],
                        "security_verified": ann.get("security_verified", False)
                    }
                    for ann in annotations
                ],
                "security_audit": [
                    {
                        "operation": audit.get("operation_type"),
                        "user": audit.get("user_id"),
                        "totp_verified": audit.get("success", False),
                        "timestamp": audit.get("created_at"),
                        "annotation_type": audit.get("annotation_type")
                    }
                    for audit in security_audit
                ]
            }
    
    def get_annotations_by_voucher(self, voucher_id: int) -> List[Dict]:
        """Get all annotations for a specific voucher"""
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM voucher_annotations
                WHERE voucher_id = ?
                ORDER BY created_at DESC
            """, (voucher_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def list_vouchers_by_period(
        self,
        start_date: str,
        end_date: str,
        include_superseded: bool = False,
        voucher_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List vouchers for a period with summary information for efficient review
        
        Args:
            start_date: Start of period (YYYY-MM-DD format)
            end_date: End of period (YYYY-MM-DD format)
            include_superseded: Whether to include superseded vouchers
            voucher_type: Optional filter for voucher type
        
        Returns:
            Dictionary containing:
            - vouchers: List of voucher summaries
            - summary: Period summary statistics
            - success: Operation status
        """
        from datetime import datetime
        
        try:
            # Parse dates
            start = datetime.strptime(start_date, "%Y-%m-%d").date()
            end = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError as e:
            return {
                "success": False,
                "error": f"Invalid date format. Use YYYY-MM-DD. {str(e)}"
            }
        
        # Use the enhanced database function
        vouchers = self.accounting_db.list_vouchers_enhanced(
            start_date=start,
            end_date=end,
            include_superseded=include_superseded,
            voucher_type=voucher_type
        )
        
        # Calculate summary statistics
        total_amount = sum(v.get('total_amount', 0) or 0 for v in vouchers)
        posted_count = sum(1 for v in vouchers if v.get('is_posted'))
        pending_count = sum(1 for v in vouchers if not v.get('is_posted') and v.get('status') != 'SUPERSEDED')
        superseded_count = sum(1 for v in vouchers if v.get('status') == 'SUPERSEDED')
        unbalanced_count = sum(1 for v in vouchers if not v.get('is_balanced'))
        
        # Get voucher type breakdown
        type_breakdown = {}
        for v in vouchers:
            vtype = v.get('voucher_type', 'Unknown')
            if vtype not in type_breakdown:
                type_breakdown[vtype] = {"count": 0, "amount": 0}
            type_breakdown[vtype]["count"] += 1
            type_breakdown[vtype]["amount"] += v.get('total_amount', 0) or 0
        
        return {
            "success": True,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "vouchers": [
                {
                    "id": v["id"],
                    "voucher_number": v.get("voucher_number"),
                    "date": v.get("voucher_date"),
                    "description": v.get("description"),
                    "type": v.get("voucher_type"),
                    "amount": v.get("total_amount"),
                    "status": v.get("status") or "ACTIVE",
                    "posting_status": v.get("posting_status"),
                    "is_posted": v.get("is_posted"),
                    "is_balanced": v.get("is_balanced"),
                    "journal_entries_count": v.get("journal_entries_count", 0),
                    "reference": v.get("reference"),
                    "source": {
                        "invoice_id": v.get("source_invoice_id"),
                        "expense_id": v.get("source_expense_id"),
                        "reminder_id": v.get("source_reminder_id")
                    },
                    "superseded_by": v.get("superseded_by"),
                    "created_at": v.get("created_at")
                }
                for v in vouchers
            ],
            "summary": {
                "total_vouchers": len(vouchers),
                "total_amount": total_amount,
                "posted": posted_count,
                "pending": pending_count,
                "superseded": superseded_count,
                "unbalanced": unbalanced_count,
                "by_type": type_breakdown
            },
            "filters": {
                "include_superseded": include_superseded,
                "voucher_type": voucher_type
            }
        }
    
    def get_superseded_vouchers(self) -> List[Dict]:
        """Get list of all superseded vouchers"""
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT v.*, va.message, va.created_at as annotation_date
                FROM vouchers v
                LEFT JOIN voucher_annotations va ON v.id = va.voucher_id
                WHERE v.status = 'SUPERSEDED' AND va.annotation_type = 'SUPERSEDED'
                ORDER BY v.id DESC
            """)
            
            return [dict(row) for row in cursor.fetchall()]
    
    def void_voucher(
        self,
        voucher_id: int,
        reason: str,
        user_id: str,
        totp_verification_id: Optional[int] = None
    ) -> Dict:
        """
        Mark voucher as void (cancelled)
        
        Args:
            voucher_id: Voucher to void
            reason: Reason for voiding
            user_id: User performing operation
            totp_verification_id: ID from successful TOTP verification
        
        Returns:
            Success/failure status
        """
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check voucher exists and status
            cursor.execute(
                "SELECT id, status, is_posted FROM vouchers WHERE id = ?",
                (voucher_id,)
            )
            voucher = cursor.fetchone()
            
            if not voucher:
                return {
                    "success": False,
                    "error": f"Voucher {voucher_id} does not exist"
                }
            
            if voucher["is_posted"]:
                return {
                    "success": False,
                    "error": "Cannot void a posted voucher. Use supersede instead."
                }
            
            # Update voucher status
            cursor.execute("""
                UPDATE vouchers SET status = 'VOID' WHERE id = ?
            """, (voucher_id,))
            
            conn.commit()
            
            # Add void annotation using internal method
            self._add_internal_annotation(
                voucher_id=voucher_id,
                annotation_type="VOID",
                message=f"Voucher voided. Reason: {reason}",
                created_by=user_id,
                security_verified=totp_verification_id is not None,
                totp_verification_id=totp_verification_id
            )
            
            return {
                "success": True,
                "voucher_id": voucher_id,
                "status": "VOID",
                "message": "Voucher voided successfully",
                "security_verified": totp_verification_id is not None
            }