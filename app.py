import csv
import os
import secrets
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse

DATA_FILE = Path(os.getenv("DATA_FILE", "records.csv"))
API_KEY = os.getenv("API_KEY", "")
app = FastAPI(title="Authorized Phone Lookup API", version="1.0.0")

def check_api_key(x_api_key: Optional[str]) -> None:
    if not API_KEY:
        raise HTTPException(status_code=503, detail="Server API_KEY is not configured.")
    if not x_api_key or not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")

def normalize_phone(value: str) -> str:
    # Keep digits only so values like +91-9876543210 can match consistently.
    return "".join(ch for ch in value if ch.isdigit())

@app.get("/health")
def health():
    return {"ok": True, "service": "authorized-phone-lookup"}

@app.get("/api/lookup")
def lookup(
    phone: str = Query(..., min_length=5, max_length=20),
    x_api_key: Optional[str] = Header(default=None),
):
    check_api_key(x_api_key)
    target = normalize_phone(phone)
    if not target:
        raise HTTPException(status_code=400, detail="Provide a valid phone number.")

    if not DATA_FILE.exists():
        raise HTTPException(status_code=503, detail=f"Data file not found: {DATA_FILE.name}")

    matches = []
    # Intended for records you own or are authorized to process.
    # For large datasets, import authorized records into a database with an indexed phone column.
    with DATA_FILE.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "phoneNumber" not in reader.fieldnames:
            raise HTTPException(status_code=500, detail="CSV must contain a phoneNumber column.")
        for row in reader:
            if normalize_phone(row.get("phoneNumber", "")) == target:
                matches.append(row)

    if not matches:
        return JSONResponse(
            status_code=404,
            content={"success": True, "matched": False, "message": "No matching authorized record found."},
        )

    # Return every column in the matching row(s), from the authorized CSV.
    return {"success": True, "matched": True, "count": len(matches), "data": matches}
