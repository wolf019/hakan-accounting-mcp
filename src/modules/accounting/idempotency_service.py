"""
Journal Entry Idempotency Service - Prevents duplicate journal entries
"""

import hashlib
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from ...database import DatabaseManager


class JournalEntryIdempotency:
    """Handles duplicate prevention for journal entries using content-based hashing"""
    
    def __init__(self, db: DatabaseManager, window_seconds: int = 30):
        """
        Initialize idempotency service
        
        Args:
            db: Database manager instance
            window_seconds: Time window for duplicate detection (default: 30 seconds)
        """
        self.db = db
        self.window_seconds = window_seconds
    
    def generate_request_hash(self, voucher_id: int, account_number: str, 
                            description: str, debit_amount: Decimal, 
                            credit_amount: Decimal, reference: Optional[str] = None) -> str:
        """
        Generate deterministic hash from request parameters
        
        Args:
            voucher_id: Target voucher ID
            account_number: Account number (e.g., "5420")
            description: Journal entry description
            debit_amount: Debit amount
            credit_amount: Credit amount
            reference: Optional reference
            
        Returns:
            16-character hash string
        """
        # Normalize amounts to ensure consistent hashing
        debit_str = f"{debit_amount:.2f}"
        credit_str = f"{credit_amount:.2f}"
        ref_str = reference or ""
        
        # Create deterministic content string
        content = f"{voucher_id}:{account_number}:{description}:{debit_str}:{credit_str}:{ref_str}"
        
        # Generate SHA-256 hash and return first 16 characters
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def check_duplicate(self, request_hash: str) -> Optional[int]:
        """
        Check if this request was processed recently
        
        Args:
            request_hash: Hash of the request parameters
            
        Returns:
            Entry ID if duplicate found, None otherwise
        """
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT entry_id FROM journal_entry_requests 
                WHERE request_hash = ? AND expires_at > datetime('now')
            """, (request_hash,))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def record_request(self, request_hash: str, entry_id: int, voucher_id: int, 
                      account_number: str):
        """
        Record successful request for duplicate detection
        
        Args:
            request_hash: Hash of the request parameters
            entry_id: Created journal entry ID
            voucher_id: Target voucher ID
            account_number: Account number used
        """
        expires_at = datetime.now() + timedelta(seconds=self.window_seconds)
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO journal_entry_requests 
                (request_hash, entry_id, voucher_id, account_number, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (request_hash, entry_id, voucher_id, account_number, expires_at))
            conn.commit()
    
