import sys
from dotenv import load_dotenv
import os
import logging
import streamlit as st
import pandas as pd
import json
import time
import openai

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

# Function to query OpenAI API
def query_openai(prompt):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    logging.debug(f"Querying OpenAI with prompt: {prompt}")
    response = openai.Completion.create(
        engine="davinci-codex",
        prompt=prompt,
        max_tokens=150
    )
    logging.debug(f"OpenAI response: {response}")
    return response.choices[0].text.strip()

# Chat with General Ledger Data
st.subheader("Chat with your General Ledger Data")
user_query = st.text_input("Enter your question about the general ledger data:")
if st.button("Submit Query"):
    if user_query:
        if 'df' in locals():
            # Create a prompt for the OpenAI API
            prompt = f"General Ledger Data:\n{df.head(5).to_string()}\n\nUser Query: {user_query}\n\nResponse:"
            response = query_openai(prompt)
            st.write("Response:")
            st.write(response)
        else:
            st.write("Please upload the general ledger data first.")
    else:
        st.write("Please enter a query.")

# Step 1: Upload General Ledger File
uploaded_file = st.file_uploader("Upload your general ledger file", type=["csv", "xlsx"])

if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    
    st.write("General Ledger Data:")
    st.dataframe(df)

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
