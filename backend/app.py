from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import uvicorn
from signer import PDFSigner
from verifier import PDFVerifier
from database import DocumentDB

app = FastAPI(title="InkCrypt API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

signer = PDFSigner()
verifier = PDFVerifier()
db = DocumentDB()

@app.post("/sign")
async def sign_pdf(file: UploadFile = File(...)):
    """Sign a PDF document"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    pdf_bytes = await file.read()
    signed_pdf, uuid = signer.sign_pdf(pdf_bytes)
    
    return Response(
        content=signed_pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=signed_{file.filename}",
            "X-InkCrypt-UUID": uuid
        }
    )

@app.post("/verify")
async def verify_pdf(file: UploadFile = File(...)):
    """Verify a PDF document"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(400, "Only PDF files are supported")
    
    pdf_bytes = await file.read()
    result = verifier.verify_pdf(pdf_bytes)
    return result

@app.post("/revoke")
async def revoke_document(uuid: str = Form(...)):
    """Revoke a document by UUID"""
    success = db.revoke_document(uuid)
    if success:
        return {"success": True, "message": "Document revoked"}
    else:
        raise HTTPException(404, "Document not found")

@app.get("/")
async def root():
    return {"message": "InkCrypt API is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)