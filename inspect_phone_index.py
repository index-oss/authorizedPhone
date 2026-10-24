import pyarrow.parquet as pq
import fsspec

from huggingface_hub import HfApi, hf_hub_url

DATASET_ID = "index-oss/reverseDomain"


def main():
    api = HfApi()
    info = api.dataset_info(
        repo_id=DATASET_ID,
        files_metadata=True,
    )

    files = [
        item.rfilename
        for item in (info.siblings or [])
        if item.rfilename.startswith("idx_phone.")
        and item.rfilename.endswith(".parquet")
    ]

    print(f"Dataset: {DATASET_ID}")
    print(f"Phone index files: {len(files)}")

    for filename in files:
        print(f"\nInspecting: {filename}")

        url = hf_hub_url(
            repo_id=DATASET_ID,
            filename=filename,
            repo_type="dataset",
        )

        try:
            with fsspec.open(
                url,
                "rb",
                block_size=1024 * 1024,
            ) as remote_file:
                parquet = pq.ParquetFile(remote_file)

                print("Schema:")
                print(parquet.schema)

                print("Rows:", parquet.metadata.num_rows)
                print(
                    "Row groups:",
                    parquet.metadata.num_row_groups,
                )

        except Exception as exc:
            print("Inspection failed:", type(exc).__name__)
            print(str(exc)[:300])


if __name__ == "__main__":
    main()
