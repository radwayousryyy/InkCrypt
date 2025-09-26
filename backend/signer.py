import hashlib
import os
import io
from typing import Tuple
from pypdf import PdfWriter, PdfReader
from database import DocumentDB

class PDFSigner:
    def __init__(self):
        self.db = DocumentDB()
        self.cert_path = "certs/signer.p12"
        self.ensure_certificate()
    
    def ensure_certificate(self):
        """Create self-signed certificate if not exists"""
        if not os.path.exists("certs"):
            os.makedirs("certs")
        
        if not os.path.exists(self.cert_path):
            self.create_self_signed_cert()
    
    def create_self_signed_cert(self):
        """Generate self-signed certificate for testing"""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization, hashes
        from cryptography.hazmat.primitives.serialization import pkcs12
        from cryptography import x509
        import datetime
        
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048
        )
        
        subject = issuer = x509.Name([
            x509.NameAttribute(x509.NameOID.COMMON_NAME, "InkCrypt Signer"),
            x509.NameAttribute(x509.NameOID.ORGANIZATION_NAME, "InkCrypt"),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.datetime.utcnow()
        ).not_valid_after(
            datetime.datetime.utcnow() + datetime.timedelta(days=365)
        ).sign(private_key, hashes.SHA256())
        
        # Save as PKCS12
        p12_data = pkcs12.serialize_key_and_certificates(
            name=b"InkCrypt",
            key=private_key,
            cert=cert,
            cas=None,
            encryption_algorithm=serialization.NoEncryption()
        )
        
        with open(self.cert_path, "wb") as f:
            f.write(p12_data)
    
    def calculate_original_hash(self, pdf_bytes: bytes) -> str:
        """Calculate hash of original PDF content without metadata"""
        return hashlib.sha256(pdf_bytes).hexdigest()
    
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
    
    def sign_pdf(self, pdf_bytes: bytes) -> Tuple[bytes, str]:
        """Sign PDF and return signed PDF bytes and UUID"""
        # Calculate hash of original content (before adding metadata)
        content_hash = self.calculate_content_hash(pdf_bytes)
        
        # Save to database first
        doc_uuid = self.db.save_document(content_hash)
        
        # Add UUID to PDF metadata
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        
        for page in reader.pages:
            writer.add_page(page)
        
        # Add UUID to metadata
        writer.add_metadata({'/InkCryptUUID': doc_uuid})
        
        # Write modified PDF
        output_buffer = io.BytesIO()
        writer.write(output_buffer)
        signed_pdf = output_buffer.getvalue()
        
        return signed_pdf, doc_uuid