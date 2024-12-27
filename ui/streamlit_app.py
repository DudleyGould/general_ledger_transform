import sys
from dotenv import load_dotenv
import os
import logging
import streamlit as st
import pandas as pd
import json
import time

# Load environment variables from .env file
load_dotenv()

# Check if the key is loaded
if not os.getenv("OPENAI_API_KEY"):
    raise EnvironmentError("OPENAI_API_KEY is not set or loaded correctly.")

# Add the project root to Python's search path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_ingestion import load_data, save_data
from src.field_mapping import suggest_field_mappings
from src.transformations import normalize_data
from src.validation import validate_data

# Configure logging to output to the console
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  # Output logs to the console
    ],
)

# Load Target Schema
with open("target_schema.json") as f:
    target_schema = json.load(f)

st.title("AI-Powered General Ledger Transformation Tool")

# Step 1: Upload General Ledger File
uploaded_file = st.file_uploader("Upload your general ledger file (CSV/Excel)")
if uploaded_file:
    try:
        st.info("Loading your file...")
        time.sleep(1)  # Simulate loading time
        df = pd.read_csv(uploaded_file)
        logging.info("Uploaded file loaded successfully.")
        logging.debug(f"Input columns: {df.columns.tolist()}")
        st.success("File loaded successfully!")
    except Exception as e:
        logging.error(f"Error loading uploaded file: {e}")
        st.error(f"Error loading file: {e}")

    st.write("Preview of Uploaded Data:")
    st.dataframe(df.head())

    # Step 2: Suggest Field Mappings
    st.subheader("AI-Generated Field Mappings")
    with st.spinner("AI is analyzing your data..."):
        time.sleep(2)  # Simulate AI processing
        input_columns = df.columns.tolist()
        mappings = suggest_field_mappings(input_columns, target_schema)
        logging.info("Field mappings suggested successfully.")
        logging.debug(f"Suggested mappings: {mappings}")
    st.success("AI has completed its analysis!")
    st.write("Suggested Mappings:")
    st.json(mappings)

    # Allow User to Approve/Edit Mappings with Pre-filled Options
    st.subheader("Review and Confirm Mappings")
    target_fields = [None] + [field['name'] for field in target_schema['attributes']]
    approved_mappings = {}

    for mapping in mappings:
        input_field = mapping["input_field"]
        recommended_target = mapping["mapped_to"]

        # Prefill dropdown with the recommended mapping
        recommended_index = target_fields.index(recommended_target) if recommended_target in target_fields else 0
        approved_mappings[input_field] = st.selectbox(
            f"Map '{input_field}' to:",
            options=target_fields,
            index=recommended_index
        )

    # Step 3: Apply Transformations
    if st.button("Apply Transformations"):
        st.info("Applying transformations...")
        progress_bar = st.progress(0)
        for i in range(1, 101):
            time.sleep(0.01)  # Simulate processing progress
            progress_bar.progress(i)

        # Update target schema with user-approved mappings
        transformed_target_schema = target_schema.copy()
        for field in transformed_target_schema["attributes"]:
            field_name = field["name"]
            if field_name in approved_mappings:
                field["mapped_to"] = approved_mappings[field_name]

        try:
            transformed_df = normalize_data(df, transformed_target_schema, approved_mappings)
            logging.info("Data transformation successful.")
            st.success("Transformation completed successfully!")
            st.write("Transformed Data Preview:")
            st.dataframe(transformed_df.head())
        except Exception as e:
            logging.error(f"Error during transformation: {e}")
            st.error(f"Error during transformation: {e}")

        # Step 4: Validation
        st.subheader("Validation Results")
        validation_issues = validate_data(transformed_df, transformed_target_schema)
        if validation_issues:
            st.error("Validation Issues Found:")
            st.write(validation_issues)
        else:
            st.success("No Validation Issues Found!")

        # Mapping Summary
        mapped_fields = {k: v for k, v in approved_mappings.items() if v is not None}
        unmapped_original_fields = [field for field in df.columns if field not in mapped_fields]
        empty_target_fields = [
            field["name"]
            for field in target_schema["attributes"]
            if field["name"] not in mapped_fields.values()
        ]

        st.subheader("Mapping Summary")
        st.write("Mapped Fields:")
        st.json(mapped_fields)
        st.write("Unmapped Original Fields:")
        st.json(unmapped_original_fields)
        st.write("Fields in Target Dataset Not in Original Dataset:")
        st.json(empty_target_fields)

        # Step 5: Download Transformed Data
        st.download_button("Download Transformed Data", data=transformed_df.to_csv(index=False), file_name="transformed_general_ledger.csv")
