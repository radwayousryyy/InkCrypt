# InkCrypt - PDF Digital Signature System

Secure PDF signing and verification using PAdES signatures with redundant validation layers.

## Features
- Invisible PAdES digital signatures
- UUID-based document tracking
- Real-time verification API
- Clean web interface

## Quick Start
1. Install dependencies: `pip install -r backend/requirements.txt`
2. Run backend: `python backend/app.py`
3. Open `frontend/index.html` in browser

## API Endpoints
- POST `/sign` - Sign PDF document
- POST `/verify` - Verify PDF authenticity
- POST `/revoke` - Revoke document by UUID

#python backend/app.py
#start index.html
