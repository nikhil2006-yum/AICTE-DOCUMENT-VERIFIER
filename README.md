# AICTE Document Verifier

**AI-Powered Application Validation, Document Authentication and Regulatory Compliance Verification**

AICTE Document Verifier is a prototype backend designed to support the validation and management of documents submitted for technical education regulatory processes. The project aims to streamline document submission, review-status tracking, audit logging, and the generation of downloadable validation reports.

> **Project status:** Prototype. Automated digital-signature authentication, trusted-source verification, and complete AICTE regulatory compliance checks are not yet implemented.

## Key Features

- **PDF Upload:** Accepts PDF documents through a REST API.
- **Document Management:** Stores document metadata and review status in an SQLite database.
- **Validation Status Tracking:** Supports verified, mismatch detected, expired, pending verification, source unavailable, and manual review required statuses.
- **Audit Trail:** Records document uploads and status changes with timestamps.
- **PDF Report Generation:** Generates downloadable reports containing document details, current status, review notes, timestamps, and audit history.
- **REST API:** Provides endpoints for uploading, listing, retrieving, and updating document records.
- **Interactive API Documentation:** Uses FastAPI's Swagger UI for testing endpoints.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| FastAPI | REST API framework |
| Uvicorn | ASGI server |
| SQLite | Document metadata and audit storage |
| Pydantic | Request validation |
| ReportLab | PDF report generation |
| Python Multipart | File upload handling |

## Project Workflow

1. Upload a PDF document.
2. Perform the prototype's initial file-header check.
3. Store document metadata and the review result in SQLite.
4. Track document status changes and audit events.
5. Retrieve document information through the REST API.
6. Generate and download a PDF report for the selected document.

## Project Structure

```text
DOCUMENT-VERIFIER/
├── main.py
├── requirements.txt
├── README.md
├── .gitignore
├── docs.db             # Generated locally
└── uploads/            # Uploaded PDFs, stored locally
```

The database and uploaded documents are local runtime files and should not be committed to Git.

## Installation and Setup

### Prerequisites

- Python 3.10 or later
- Git
- pip

### 1. Clone the repository

```bash
git clone https://github.com/nikhil2006-yum/AICTE-DOCUMENT-VERIFIER.git
cd AICTE-DOCUMENT-VERIFIER
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Start the backend

```bash
python -m uvicorn main:app --reload
```

The backend should be available at:

- **API base URL:** http://127.0.0.1:8000
- **Swagger documentation:** http://127.0.0.1:8000/docs
- **ReDoc documentation:** http://127.0.0.1:8000/redoc

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/documents` | Upload a PDF document |
| GET | `/documents` | List stored documents |
| GET | `/documents/{doc_id}` | Retrieve document details and audit history |
| PATCH | `/documents/{doc_id}/flag` | Update review status and notes |
| GET | `/documents/{doc_id}/report` | Generate a downloadable PDF report |

### Example: Upload a Document

Use `POST /documents` in Swagger UI. Select a PDF and execute the request.

A successful response includes the document ID, filename, review result, and status.

### Example: Update a Document Status

```json
{
  "flag": "manual_review_required",
  "note": "Further verification is required"
}
```

### Generate a Report

After uploading a document, copy its ID from the response and open:

```text
http://127.0.0.1:8000/documents/YOUR_DOCUMENT_ID/report
```

Replace `YOUR_DOCUMENT_ID` with the actual document ID.

## Validation Statuses

- `verified`
- `mismatch_detected`
- `expired`
- `verification_pending`
- `source_unavailable`
- `manual_review_required`

These statuses are supported by the prototype's data model. Their presence does not mean every corresponding validation check has been implemented.

## Current Limitations

- The current review verdict is controlled by a mock configuration.
- Checking a PDF header does not establish that the entire file is valid or authentic.
- Cryptographic digital-signature verification is not yet implemented.
- Signer identity and certificate-chain validation are not yet implemented.
- Trusted AICTE record matching and automated regulatory compliance checks remain future development tasks.
- Expiry detection and automated alert notifications are not yet implemented.
- Authentication, authorization, and production-grade file security need to be added before deployment.

**Important:** A PDF containing an image of a signature is not equivalent to a cryptographically signed PDF. The prototype's `verified` status must not be treated as proof of authenticity.

## Future Enhancements

- Digital-signature and certificate validation.
- Document text extraction and field comparison.
- Integration with trusted regulatory records.
- Configurable AICTE compliance rules.
- Automated alerts for mismatches, missing documents, and manual review.
- Enhanced validation reports with individual check results and supporting evidence.
- User authentication, role-based access control, and secure deployment.

## Disclaimer

This is a prototype developed for demonstrating a potential document-validation workflow. It is not an official AICTE service and does not certify document authenticity or regulatory compliance.

## Repository

[GitHub — AICTE-DOCUMENT-VERIFIER](https://github.com/nikhil2006-yum/AICTE-DOCUMENT-VERIFIER)
