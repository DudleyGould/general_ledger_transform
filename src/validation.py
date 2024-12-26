def validate_data(df, schema):
    """Validates that the DataFrame matches the target schema."""
    issues = []
    for field in schema["attributes"]:
        if field["name"] not in df.columns or df[field["name"]].isnull().all():
            issues.append(f"Missing or empty field: {field['name']}")
    return issues
