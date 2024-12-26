import pandas as pd
import logging

def normalize_data(df, target_schema, approved_mappings):
    """
    Transforms the input DataFrame to match the target schema using the approved mappings.
    
    :param df: Input DataFrame
    :param target_schema: Target schema definition
    :param approved_mappings: Dictionary of approved mappings {input_field: target_field}
    :return: Transformed DataFrame
    """
    transformed_df = pd.DataFrame()

    for field in target_schema["attributes"]:
        target_field = field["name"]
        source_field = None

        for input_field, mapped_field in approved_mappings.items():
            if mapped_field == target_field:
                source_field = input_field
                break

        if source_field:
            try:
                transformed_df[target_field] = df[source_field]
                logging.info(f"Mapped '{source_field}' to '{target_field}' successfully.")
            except KeyError:
                logging.error(f"Source field '{source_field}' not found in input data.")
                transformed_df[target_field] = None
        else:
            logging.warning(f"No mapping found for target field '{target_field}'. Setting as null.")
            transformed_df[target_field] = None

        if field["dataType"] == "datetime":
            try:
                transformed_df[target_field] = pd.to_datetime(transformed_df[target_field])
            except Exception as e:
                logging.error(f"Error converting '{target_field}' to datetime: {e}")
        elif field["dataType"] == "decimal":
            try:
                transformed_df[target_field] = pd.to_numeric(transformed_df[target_field], errors="coerce")
            except Exception as e:
                logging.error(f"Error converting '{target_field}' to decimal: {e}")

    return transformed_df
