import os
import sys
import json
import logging
from datetime import datetime

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Add the project root to Python's search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import modules from the `src` package
try:
    from src.data_ingestion import load_data, save_data
    from src.field_mapping import suggest_field_mappings
    from src.transformations import normalize_data
    from src.validation import validate_data
except ModuleNotFoundError as e:
    raise ModuleNotFoundError(
        "The 'src' module could not be found. Ensure your project directory structure is correct "
        "and the `src` folder contains the required Python files with a valid `__init__.py`."
    ) from e

# Load environment variables
load_dotenv()

# Verify OpenAI API Key
if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError("OPENAI_API_KEY is not set or loaded correctly.")

# Set up logging
log_filename = f"logs/streamlit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logging.getLogger().addHandler(logging.StreamHandler())  # Stream logs to console

# Load Target Schema
with open("target_schema.json", "r") as f:
    target_schema = json.load(f)

# Streamlit App Title
st.title("General Ledger Transformation Tool")

# Step 1: File Upload
uploaded_file = st.file_uploader("Upload your general ledger file (CSV/Excel)")
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        logging.info("Uploaded file loaded successfully.")
        logging.debug(f"Input columns: {df.columns.tolist()}")
        st.write("Preview of Uploaded Data:")
        st.dataframe(df.head())
    except Exception as e:
        logging.error(f"Error loading uploaded file: {e}")
        st.error(f"Failed to load file: {e}")
        st.stop()

    # Step 2: Field Mappings
    st.subheader("Field Mappings")
    input_columns = df.columns.tolist()
    mappings = suggest_field_mappings(input_columns, target_schema)
    logging.info("Field mappings suggested successfully.")
    logging.debug(f"Suggested mappings: {mappings}")

    # Display Suggested Mappings
    target_fields = [None] + [field["name"] for field in target_schema["attributes"]]
    approved_mappings = {}
    st.write("Approve or Edit Field Mappings:")

    for mapping in mappings:
        input_field = mapping["input_field"]
        recommended_target = mapping["mapped_to"]

        # Prefill dropdown with the recommended mapping
        recommended_index = target_fields.index(recommended_target) if recommended_target in target_fields else 0
        approved_mappings[input_field] = st.selectbox(
            f"Map '{input_field}' to:",
            options=target_fields,
            index=recommended_index,
        )
    logging.info("User-approved mappings collected.")
    logging.debug(f"Approved mappings: {approved_mappings}")

    # Step 3: Apply Transformations
    if st.button("Apply Transformations"):
        try:
            # Normalize Data
            transformed_df = normalize_data(df, target_schema, approved_mappings)
            logging.info("Transformation applied successfully.")
            logging.debug(f"Transformed data preview: {transformed_df.head().to_dict()}")
            st.write("Transformed Data:")
            st.dataframe(transformed_df.head())

            # Step 4: Summary Report
            st.subheader("Transformation Summary")
            mapped_fields = [
                {"Original Field": k, "Mapped To": v}
                for k, v in approved_mappings.items()
                if v is not None
            ]

            unmapped_fields = [
                col for col in input_columns if col not in approved_mappings or not approved_mappings[col]
            ]

            empty_target_fields = [
                field["name"] for field in target_schema["attributes"]
                if field["name"] not in transformed_df.columns or transformed_df[field["name"]].isnull().all()
            ]

            # Display the summary
            st.write("### Mapped Fields")
            st.table(pd.DataFrame(mapped_fields))

            st.write("### Unmapped Original Fields")
            st.write(unmapped_fields)

            st.write("### Empty or Missing Target Fields")
            st.write(empty_target_fields)

            # Step 5: Download Transformed Data
            csv_data = transformed_df.to_csv(index=False)
            st.download_button(
                label="Download Transformed Data",
                data=csv_data,
                file_name="transformed_general_ledger.csv",
            )
        except Exception as e:
            logging.error(f"Error during transformation or validation: {e}")
            st.error(f"Transformation failed: {e}")
