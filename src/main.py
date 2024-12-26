import sys
from dotenv import load_dotenv
import os

load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))




from src.data_ingestion import load_data
from src.field_mapping import suggest_field_mappings
import json

if __name__ == "__main__":
    # Load data
    file_path = "data/sample_general_ledger.csv"
    df = load_data(file_path)

    # Display loaded data
    print("Data Loaded:")
    print(df.head())

    # Load target schema
    with open("target_schema.json") as schema_file:
        target_schema = json.load(schema_file)

    # Suggest field mappings
    input_columns = df.columns.tolist()
    mappings = suggest_field_mappings(input_columns, target_schema)
    print("Suggested Field Mappings:")
    print(mappings)
