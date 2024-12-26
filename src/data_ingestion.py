import pandas as pd

def load_data(file_path):
    """Loads a CSV file into a Pandas DataFrame."""
    try:
        df = pd.read_csv(file_path)
        return df
    except Exception as e:
        raise Exception(f"Error loading data: {e}")

def save_data(df, output_path):
    """Saves a Pandas DataFrame to a CSV file."""
    try:
        df.to_csv(output_path, index=False)
    except Exception as e:
        raise Exception(f"Error saving data: {e}")
