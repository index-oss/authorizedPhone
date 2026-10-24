# Authorized Phone Lookup API

A small FastAPI service for looking up rows in a CSV containing records you own or are authorized to process. It is intentionally protected by an API key. Do not load or expose other people's sensitive personal data without valid authorization and a lawful basis.

## 1. Local setup

Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

Set an API key before starting.

Windows PowerShell:
```powershell
$env:API_KEY="replace-with-a-long-random-secret"
$env:DATA_FILE="records.csv"
uvicorn app:app --reload
```

Linux/macOS:
```bash
export API_KEY="replace-with-a-long-random-secret"
export DATA_FILE="records.csv"
uvicorn app:app --reload
```

## 2. Data format

Use a CSV with a `phoneNumber` column. Other columns are returned with the matching row. Replace the sample `records.csv` with your own authorized records. The example row is fake.

For very large files, this CSV scan is only a starter implementation and will be slow. Move authorized records into PostgreSQL or SQLite and add an index on a normalized phone-number column before production use. Do not put a 227 GB dataset into a free web-service filesystem or memory.

## 3. Test

Health:
```bash
curl http://127.0.0.1:8000/health
```

Lookup:
```bash
curl -H "X-API-Key: replace-with-a-long-random-secret" \
  "http://127.0.0.1:8000/api/lookup?phone=9999999999"
```

Interactive API docs are at `/docs` while running locally.

## 4. Deploy to Render

1. Push the project to a private GitHub repository.
2. Create a Render Web Service from that repository.
3. Add `API_KEY` as a secret environment variable in Render.
4. Do not commit real records or `.env` to GitHub.
5. Ensure your data source is authorized and accessible to the service.

The included `render.yaml` is a starter configuration. A free Render instance may sleep and has limited disk, memory, and runtime; it cannot host a 227 GB dataset directly.

## Security notes

- Keep the service private or protected; API keys are not a substitute for authorization and rate limits.
- Never return Aadhaar numbers, passwords, or other highly sensitive fields from a public endpoint.
- Use only records you own or are authorized to process.
