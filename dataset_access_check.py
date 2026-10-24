from huggingface_hub import HfApi

DATASET_ID = "index-oss/reverseDomain"


def main():
    api = HfApi()

    print("Checking Hugging Face dataset access...")

    try:
        info = api.dataset_info(
            repo_id=DATASET_ID,
            files_metadata=True,
        )

        print("\nAccess successful!")
        print(f"Dataset: {info.id}")
        print(f"Revision: {info.sha}")

        files = info.siblings or []
        parquet_files = [
            file.rfilename
            for file in files
            if file.rfilename.endswith(".parquet")
        ]

        print(f"\nParquet files found: {len(parquet_files)}")

        for filename in parquet_files:
            print(f"- {filename}")

        if not parquet_files:
            print(
                "\nNo Parquet files found in the "
                "repository listing."
            )

    except Exception as exc:
        print("\nDataset access failed.")
        print(f"Error type: {type(exc).__name__}")
        print("Check the dataset ID, network, and permissions.")


if __name__ == "__main__":
    main()
