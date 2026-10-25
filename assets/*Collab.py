import duckdb
import os

# Input the phone number you want to search
SEARCH_NUMBER = "7800206151"  # Yahan apna number change karein

DATASET_ID = os.getenv("HF_DATASET_ID", "index-oss/reverseDomain")

def search_phone_number(phone_num):
    # Clean the input phone number (keep only digits)
    cleaned_num = "".join(filter(str.isdigit, str(phone_num)))
    if not cleaned_num:
        print("Kripya ek valid phone number enter karein!")
        return

    print(f"Searching for {cleaned_num} across dataset files...")
    
    # Setup DuckDB connection
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs;")
    
    # We construct the path for all 7 parquet files
    # Using 'hf://' protocol supported by DuckDB for Hugging Face
    urls = [f"hf://datasets/{DATASET_ID}/idx_phone.{i}.parquet" for i in range(7)]
    
    found = False
    for url in urls:
        filename = url.split('/')[-1]
        try:
            # Query to check if the phone number exists in the current file
            query = """
                SELECT * 
                FROM read_parquet(?)
                WHERE phoneNumber = ?
                LIMIT 1
            """
            result_df = con.execute(query, [url, cleaned_num]).df()
            
            if not result_df.empty:
                print(f"\n🎉 Match found in file: {filename}!")
                display(result_df)
                found = True
                break
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            
    if not found:
        print(f"\nNo match found for phone number: {cleaned_num}")

# Run the search function
search_phone_number(SEARCH_NUMBER)
