from langchain_openai.chat_models import ChatOpenAI
import os
import json

def suggest_field_mappings(input_columns, target_schema):
    """Suggests field mappings between input columns and the target schema."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY is not set or loaded correctly.")

    llm = ChatOpenAI(model="gpt-4", temperature=0, openai_api_key=api_key)
    prompt = (
        f"Map the following fields: {input_columns} to the target schema: {target_schema['attributes']}. "
        "Respond with valid JSON in this format: "
        '{"mappings": [{"input_field": "field_name", "mapped_to": "target_field_name", "confidence": "percentage"}]}. '
        "Leave fields blank if you are less than 90% confident in the mapping."
    )

    response = llm.invoke([{"role": "user", "content": prompt}])

    # Parse the response content
    try:
        response_json = json.loads(response.content)
        mappings = response_json["mappings"]

        # Filter mappings based on confidence level
        filtered_mappings = []
        for mapping in mappings:
            confidence_str = mapping.get("confidence", "").rstrip('%')  # Remove % and handle missing keys
            if confidence_str.isdigit():  # Check if confidence is a valid number
                confidence = int(confidence_str)
            else:
                confidence = 0  # Default to 0 if invalid or missing

            filtered_mappings.append({
                "input_field": mapping["input_field"],
                "mapped_to": mapping["mapped_to"] if confidence >= 90 else None
            })
        return filtered_mappings
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse response as JSON: {response.content}") from e
