import os
from dataclasses import dataclass

import fsspec
import pyarrow.parquet as pq
from huggingface_hub import HfApi, hf_hub_url


DATASET_ID = os.getenv("HF_DATASET_ID", "index-oss/reverseDomain")
PHONE_INDEX_PREFIX = "idx_phone."
MAX_FILES_TO_INSPECT = int(os.getenv("MAX_FILES_TO_INSPECT", "7"))


@dataclass
class ParquetFileInfo:
    filename: str
    rows: int
    row_groups: int
    schema: str


def get_hf_files():
    """Return phone-index Parquet filenames."""
    token = os.getenv("HF_TOKEN") or None
    api = HfApi(token=token)

    info = api.dataset_info(
        repo_id=DATASET_ID,
        repo_type="dataset",
        files_metadata=True,
    )

    return sorted(
        item.rfilename
        for item in (info.siblings or [])
        if item.rfilename.startswith(PHONE_INDEX_PREFIX)
        and item.rfilename.endswith(".parquet")
    )


def inspect_parquet_file(filename: str) -> ParquetFileInfo:
    """Read remote Parquet metadata without downloading the full file."""
    token = os.getenv("HF_TOKEN") or None

    url = hf_hub_url(
        repo_id=DATASET_ID,
        filename=filename,
        repo_type="dataset",
    )

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    with fsspec.open(
        url,
        "rb",
        block_size=1024 * 1024,
        headers=headers,
    ) as remote_file:
        parquet = pq.ParquetFile(remote_file)
        metadata = parquet.metadata

        return ParquetFileInfo(
            filename=filename,
            rows=metadata.num_rows,
            row_groups=metadata.num_row_groups,
            schema=str(parquet.schema),
        )


def inspect_phone_index():
    """Inspect index structure and report metadata."""
    files = get_hf_files()

    if not files:
        raise RuntimeError(
            f"No phone-index Parquet files found in dataset: {DATASET_ID}"
        )

    results = []

    for filename in files[:MAX_FILES_TO_INSPECT]:
        try:
            result = inspect_parquet_file(filename)
            results.append(result)

            print(f"\nFile: {result.filename}")
            print(f"Rows: {result.rows:,}")
            print(f"Row groups: {result.row_groups}")
            print(f"Schema:\n{result.schema}")

        except Exception as exc:
            print(
                f"Failed to inspect {filename}: "
                f"{type(exc).__name__}: {exc}"
            )

    return results


if __name__ == "__main__":
    results = inspect_phone_index()

    print("\nInspection summary")
    print(f"Files inspected successfully: {len(results)}")
    print(f"Dataset: {DATASET_ID}")
