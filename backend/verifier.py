import hashlib
import io
from typing import Dict, Any
from pypdf import PdfReader, PdfWriter
from database import DocumentDB

class PDFVerifier:
    def __init__(self):
        self.db = DocumentDB()
    
    def calculate_content_hash(self, pdf_bytes: bytes) -> str:
        """Calculate hash of PDF content (used for integrity check)"""
        # Remove metadata for consistent hashing
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            writer = PdfWriter()
            
            # Copy pages without metadata
            for page in reader.pages:
                writer.add_page(page)
            
            # Get clean PDF bytes
            clean_buffer = io.BytesIO()
            writer.write(clean_buffer)
            clean_bytes = clean_buffer.getvalue()
            
            return hashlib.sha256(clean_bytes).hexdigest()
        except:
            # Fallback to original bytes if PDF processing fails
            return hashlib.sha256(pdf_bytes).hexdigest()
    
    def extract_uuid(self, pdf_bytes: bytes) -> str:
        """Extract UUID from PDF metadata"""
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            metadata = reader.metadata
            if metadata and '/InkCryptUUID' in metadata:
                return str(metadata['/InkCryptUUID'])
        except Exception:
            pass
        return None
    
    def verify_pdf(self, pdf_bytes: bytes) -> Dict[str, Any]:
        """Verify PDF authenticity"""
        try:
            # Extract UUID
            uuid = self.extract_uuid(pdf_bytes)
            if not uuid:
                return {
                    'valid': False,
                    'reason': 'No InkCrypt signature found',
                    'confidence': 'INVALID'
                }
            
            # Get document record
            doc_record = self.db.get_document(uuid)
            if not doc_record:
                return {
                    'valid': False,
                    'reason': 'Document UUID not found in database',
                    'confidence': 'INVALID'
                }
            
            # Check if revoked
            if doc_record['status'] == 'REVOKED':
                return {
                    'valid': False,
                    'reason': 'Document has been revoked',
                    'confidence': 'REVOKED'
                }
            
            # Verify content hash (excluding metadata)
            current_hash = self.calculate_content_hash(pdf_bytes)
            if current_hash != doc_record['doc_hash']:
                return {
                    'valid': False,
                    'reason': 'Document content has been modified',
                    'confidence': 'TAMPERED'
                }
            
            return {
                'valid': True,
                'reason': 'Document is authentic',
                'confidence': 'VALID',
                'uuid': uuid,
                'signed_at': doc_record['signed_at'],
                'signer': doc_record['signer_dn']
            }
            
        except Exception as e:
            return {
                'valid': False,
                'reason': f'Verification error: {str(e)}',
                'confidence': 'ERROR'
            }