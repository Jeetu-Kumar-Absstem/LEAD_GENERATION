from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import requests
import csv
import uuid
import time
import random

from database import SessionLocal, engine
from models import Lead, Base, InputFile, OutputFile
from utils import extract_domain, flatten_emails

from dotenv import load_dotenv
import os
load_dotenv()

HUNTER_API_KEY = os.getenv("HUNTER_API_KEY")

app = FastAPI()

# ==============================
# CORS
# ==============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# Initialize Database on Startup
# ==============================
@app.on_event("startup")
def startup_event():
    max_retries = 10
    retry_delay = 2
    for attempt in range(max_retries):
        try:
            Base.metadata.create_all(bind=engine)
            print("✅ Database tables created successfully")
            return
        except Exception as e:
            print(f"⚠️ Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise Exception("Failed to connect to database after retries")

# ==============================
# GET REMAINING CREDITS
# ==============================
def get_remaining_credits():
    try:
        url = "https://api.hunter.io/v2/account"
        params = {"api_key": HUNTER_API_KEY}

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 200:
            data = response.json()
            credits = (
                data.get("data", {})
                .get("requests", {})
                .get("credits", {})
                .get("available")
            )
            return credits

        else:
            print(f"❌ Credit API error: {response.status_code} - {response.text}")

    except Exception as e:
        print("⚠️ Credit Fetch Error:", e)

    return None


# ==============================
# GET EMAILS (WITH RETRY)
# ==============================
def get_emails(domain, retries=2):
    try:
        url = "https://api.hunter.io/v2/domain-search"

        params = {
            "domain": domain,
            "api_key": HUNTER_API_KEY,
            "limit": 10
        }

        response = requests.get(url, params=params, timeout=10)

        try:
            data = response.json()
        except:
            data = {}

        if response.status_code == 200:
            if "errors" in data:
                print(f"❌ Hunter API error for {domain}: {data['errors']}")
                return None

            return data.get("data", {}).get("emails", [])

        elif response.status_code == 429:
            if retries > 0:
                print(f"⏳ Rate limited for {domain}, retrying...")
                time.sleep(3)
                return get_emails(domain, retries - 1)

            print("❌ Hunter credits exhausted (429)")
            return "LIMIT_REACHED"

        else:
            print(f"❌ Failed {domain}: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ Exception for {domain}: {e}")
        return None


# ==============================
# UPLOAD FILE AND STORE IN DB
# ==============================
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not file:
            return {"error": "No file uploaded"}

        # Read file contents into memory
        contents = await file.read()
        
        db = SessionLocal()
        
        # Store file in input_files table
        input_file = InputFile(
            original_filename=file.filename,
            mime_type=file.content_type,
            file_size=len(contents),
            file_data=contents,
            uploaded_by="default_user"
        )
        
        db.add(input_file)
        db.commit()
        db.refresh(input_file)
        db.close()
        
        return {
            "success": True,
            "inputFileId": input_file.id,
            "filename": file.filename,
            "file_size": len(contents)
        }
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return {"error": str(e)}


# ==============================
# PROCESS FILE
# ==============================
@app.post("/process")
async def process_file(file: UploadFile = File(...)):

    batch_id = str(uuid.uuid4())

    remaining_credits = get_remaining_credits()
    credit_check_failed = False

    if remaining_credits is None:
        print("⚠️ Credit API failed → fallback mode OFF (continue normally)")
        credit_check_failed = True
    else:
        print(f"✅ Remaining credits: {remaining_credits}")

    # 🚨 IMPORTANT FIX
    LIMIT_REACHED = False
    if not credit_check_failed and remaining_credits <= 0:
        print("🚫 No credits available at start")
        LIMIT_REACHED = True

    call_count = 0

    contents = await file.read()

    # Save uploaded input file to database so Inputs tab shows it
    db = SessionLocal()
    input_file = InputFile(
        original_filename=file.filename,
        mime_type=file.content_type,
        file_size=len(contents),
        file_data=contents,
        uploaded_by="default_user",
        status="uploaded"
    )
    db.add(input_file)
    db.commit()
    db.refresh(input_file)
    input_file_id = input_file.id

    if file.filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(contents))
    else:
        df = pd.read_excel(io.BytesIO(contents))

    df.columns = df.columns.str.strip().str.lower()

    final_data = []
    domain_cache = {}

    for _, row in df.iterrows():
        try:
            company = str(row.get("company", "")).strip()
            website = row.get("website") or row.get("url") or ""
            location = row.get("location", "")

            domain = extract_domain(website)
            if not domain:
                continue

            if any(x in domain for x in ["gmail.com", "yahoo.com", "hotmail.com"]):
                continue

            # =========================
            # CACHE
            # =========================
            if domain in domain_cache:
                emails = domain_cache[domain]

            else:
                if LIMIT_REACHED:
                    emails = []
                else:
                    result = get_emails(domain)

                    if result == "LIMIT_REACHED":
                        LIMIT_REACHED = True
                        emails = []

                    elif result is None:
                        emails = []

                    else:
                        emails = result
                        domain_cache[domain] = emails
                        call_count += 1

                        print(f"✅ API CALL {call_count} → {domain}")

                        # Rate limiting protection
                        if call_count % 5 == 0:
                            time.sleep(1)
                        else:
                            time.sleep(0.5 + random.uniform(0, 0.3))

            # =========================
            # FALLBACK EMAILS (IMPROVED)
            # =========================
            if not emails:
                print(f"⚠️ Fallback used for {domain}")
                emails = [
                    {"value": f"info@{domain}", "confidence": 50},
                    {"value": f"contact@{domain}", "confidence": 50},
                    {"value": f"sales@{domain}", "confidence": 50}
                ]

            # =========================
            # FLATTEN + SAVE
            # =========================
            flattened = flatten_emails(company, domain, emails, location)

            for lead in flattened:
                final_data.append(lead)

                db.add(Lead(
                    company_name=lead.get("company"),
                    domain=lead.get("domain"),
                    email=lead.get("email"),
                    confidence=lead.get("confidence"),
                    first_name=lead.get("first_name"),
                    last_name=lead.get("last_name"),
                    position=lead.get("position"),
                    batch_id=batch_id
                ))

        except Exception as e:
            print("⚠️ Row Error:", e)

    db.commit()
    
    # ==============================
    # SAVE OUTPUT FILE TO DATABASE
    # ==============================
    # Generate CSV content in memory
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    
    writer.writerow([
        "Company", "Domain", "Email", "Confidence",
        "First Name", "Last Name", "Position"
    ])
    
    for lead in final_data:
        writer.writerow([
            lead.get("company"),
            lead.get("domain"),
            lead.get("email"),
            lead.get("confidence"),
            lead.get("first_name"),
            lead.get("last_name"),
            lead.get("position")
        ])
    
    csv_content = csv_buffer.getvalue()
    csv_bytes = csv_content.encode('utf-8')
    
    # Store output file in database
    output_filename = f"leadgen_output_{batch_id}.csv"
    output_file = OutputFile(
        input_file_id=input_file_id,
        original_filename=output_filename,
        mime_type="text/csv",
        file_size=len(csv_bytes),
        file_data=csv_bytes,
        records_generated=len(final_data),
        status="generated"
    )
    
    db.add(output_file)
    db.commit()
    db.refresh(output_file)
    db.close()

    return {
        "message": "Processed successfully",
        "batch_id": batch_id,
        "outputFileId": output_file.id,
        "credits_used": call_count,
        "data": final_data
    }


# ==============================
# DATA ENDPOINTS - LIST FILES
# ==============================
@app.get("/data/inputs")
def list_input_files():
    """List all uploaded input files"""
    db = SessionLocal()
    files = db.query(InputFile).order_by(InputFile.uploaded_at.desc()).all()
    db.close()
    
    return [{
        "id": f.id,
        "original_filename": f.original_filename,
        "file_size": f.file_size,
        "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
        "status": f.status
    } for f in files]


@app.get("/data/outputs")
def list_output_files():
    """List all generated output files"""
    db = SessionLocal()
    files = db.query(OutputFile).order_by(OutputFile.created_at.desc()).all()
    db.close()
    
    return [{
        "id": f.id,
        "original_filename": f.original_filename,
        "file_size": f.file_size,
        "created_at": f.created_at.isoformat() if f.created_at else None,
        "records_generated": f.records_generated,
        "status": f.status
    } for f in files]


# ==============================
# DATA ENDPOINTS - DOWNLOAD FILES
# ==============================
@app.get("/data/inputs/{file_id}/download")
def download_input_file(file_id: int):
    """Download an uploaded input file from database"""
    db = SessionLocal()
    file = db.query(InputFile).filter(InputFile.id == file_id).first()
    db.close()
    
    if not file:
        return {"error": "File not found"}
    
    return StreamingResponse(
        io.BytesIO(file.file_data),
        media_type=file.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={file.original_filename}"}
    )


@app.get("/data/outputs/{file_id}/download")
def download_output_file(file_id: int):
    """Download a generated output file from database"""
    db = SessionLocal()
    file = db.query(OutputFile).filter(OutputFile.id == file_id).first()
    db.close()
    
    if not file:
        return {"error": "File not found"}
    
    return StreamingResponse(
        io.BytesIO(file.file_data),
        media_type=file.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={file.original_filename}"}
    )


# ==============================
# DOWNLOAD CSV
# ==============================
@app.get("/download/{batch_id}")
def download_data(batch_id: str):
    db = SessionLocal()
    leads = db.query(Lead).filter(Lead.batch_id == batch_id).all()
    db.close()

    def generate():
        data = io.StringIO()
        writer = csv.writer(data)

        writer.writerow([
            "Company", "Domain", "Email", "Confidence",
            "First Name", "Last Name", "Position"
        ])

        for l in leads:
            writer.writerow([
                l.company_name,
                l.domain,
                l.email,
                l.confidence,
                l.first_name,
                l.last_name,
                l.position
            ])

        data.seek(0)
        yield data.read()

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=leads_{batch_id}.csv"
        }
    )