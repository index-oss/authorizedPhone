import os
import secrets
from typing import Optional

import duckdb
from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse

# Configuration
API_KEY = os.getenv("API_KEY", "")
DATASET_ID = os.getenv(
    "HF_DATASET_ID",
    "index-oss/reverseDomain",
)

app = FastAPI(
    title="Authorized Phone Lookup API",
    version="2.0.0",
)


def check_api_key(x_api_key: Optional[str]) -> None:
    if not API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Server API_KEY is not configured.",
        )

    if not x_api_key or not secrets.compare_digest(
        x_api_key, API_KEY
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key.",
        )


def normalize_phone(value: str) -> str:
    return "".join(ch for ch in str(value) if ch.isdigit())


def search_phone_number(phone_num: str):
    """
    Search the seven Hugging Face Parquet files using DuckDB.
    Returns the first matching record as a JSON-compatible dictionary.
    """

    cleaned_num = normalize_phone(phone_num)

    if not cleaned_num:
        raise HTTPException(
            status_code=400,
            detail="Provide a valid phone number.",
        )

    # Keep the original seven-file naming convention.
    urls = [
        f"hf://datasets/{DATASET_ID}/idx_phone.{i}.parquet"
        for i in range(7)
    ]

    con = None

    try:
        con = duckdb.connect()

        # Load the HTTP filesystem extension.
        con.execute("INSTALL httpfs")
        con.execute("LOAD httpfs")

        for url in urls:
            filename = url.rsplit("/", 1)[-1]

            try:
                query = """
                    SELECT *
                    FROM read_parquet(?)
                    WHERE CAST(phoneNumber AS VARCHAR) = ?
                    LIMIT 1
                """

                result_df = con.execute(
                    query,
                    [url, cleaned_num],
                ).fetchdf()

                if not result_df.empty:
                    # Convert the matching row into JSON-compatible data.
                    record = result_df.head(1).to_dict(
                        orient="records"
                    )[0]

                    # Convert special values such as NaN/NaT to None.
                    import pandas as pd

                    record = {
                        key: (
                            None
                            if pd.isna(value)
                            else value.item()
                            if hasattr(value, "item")
                            else value
                        )
                        for key, value in record.items()
                    }

                    return {
                        "success": True,
                        "matched": True,
                        "source": filename,
                        "data": record,
                    }

            except HTTPException:
                raise

            except Exception as exc:
                # A missing or inaccessible file should not silently
                # become a "no matching record" result.
                raise RuntimeError(
                    f"Could not search {filename}: {exc}"
                ) from exc

        return {
            "success": True,
            "matched": False,
            "message": "No matching authorized record found.",
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Dataset search failed: {str(exc)}",
        ) from exc

    finally:
        if con is not None:
            con.close()


@app.get("/health")
def health():
    return {
        "ok": True,
        "service": "authorized-phone-lookup",
    }


@app.get("/api/lookup")
def lookup(
    phone: str = Query(
        ...,
        min_length=5,
        max_length=20,
        description="Phone number to search",
    ),
    x_api_key: Optional[str] = Header(default=None),
):
    check_api_key(x_api_key)

    target = normalize_phone(phone)

    if not target:
        raise HTTPException(
            status_code=400,
            detail="Provide a valid phone number.",
        )

    return search_phone_number(target)
