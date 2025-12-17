import pandas as pd
from io import BytesIO

def export_to_csv(dataframe, filename="properties.csv"):
    """
    Convert DataFrame to CSV for download
    
    Returns BytesIO object for Streamlit download button
    """
    csv_buffer = BytesIO()
    dataframe.to_csv(csv_buffer, index=False, encoding='utf-8')
    csv_buffer.seek(0)
    return csv_buffer
