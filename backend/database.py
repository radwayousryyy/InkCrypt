import sqlite3
import uuid
import hashlib
from datetime import datetime
from typing import Optional, Dict

class DocumentDB:
    def __init__(self, db_path: str = "documents.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                uuid TEXT PRIMARY KEY,
                doc_hash TEXT NOT NULL,
                signature_blob BLOB,
                signer_dn TEXT,
                signed_at TIMESTAMP,
                status TEXT DEFAULT 'ACTIVE'
            )
        ''')
        conn.commit()
        conn.close()
    
    def save_document(self, doc_hash: str, signature_blob: bytes = None, 
                     signer_dn: str = "InkCrypt") -> str:
        doc_uuid = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO documents (uuid, doc_hash, signature_blob, signer_dn, signed_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (doc_uuid, doc_hash, signature_blob, signer_dn, datetime.now()))
        conn.commit()
        conn.close()
        return doc_uuid
    
    def get_document(self, doc_uuid: str) -> Optional[Dict]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM documents WHERE uuid = ?', (doc_uuid,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'uuid': row[0], 'doc_hash': row[1], 'signature_blob': row[2],
                'signer_dn': row[3], 'signed_at': row[4], 'status': row[5]
            }
        return None
    
    def revoke_document(self, doc_uuid: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE documents SET status = ? WHERE uuid = ?', 
                      ('REVOKED', doc_uuid))
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return success