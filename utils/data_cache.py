import json
import os
from datetime import datetime
import pandas as pd
import streamlit as st

DATA_DIR = "cached_data"

def ensure_data_dir():
    """Create data directory if it doesn't exist"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def save_properties_cache(df, property_type="on_market", use_google_sheets=False):
    """
    Save properties DataFrame with timestamp
    
    Args:
        df: DataFrame to save
        property_type: Type identifier (on_market, off_market, etc.)
        use_google_sheets: If True, save to Google Sheets; otherwise JSON
    
    Returns:
        timestamp string
    """
    timestamp = datetime.now().isoformat()
    
    if use_google_sheets:
        # Save to Google Sheets
        try:
            from utils.google_sheets_cache import get_google_sheets_cache
            sheets_cache = get_google_sheets_cache()
            
            if sheets_cache.is_configured():
                sheets_cache.save_properties(df, sheet_name=property_type, mode="overwrite")
                return timestamp
            else:
                st.warning("Google Sheets not configured, falling back to JSON")
        except Exception as e:
            st.error(f"Failed to save to Google Sheets: {str(e)}")
    
    # Save to JSON (default or fallback)
    ensure_data_dir()
    
    cache_data = {
        "timestamp": timestamp,
        "property_type": property_type,
        "count": len(df),
        "properties": df.to_dict(orient="records")
    }
    
    filepath = os.path.join(DATA_DIR, f"{property_type}_properties.json")
    with open(filepath, 'w') as f:
        json.dump(cache_data, f, indent=2)
    
    return timestamp

def load_properties_cache(property_type="on_market", prefer_google_sheets=False):
    """
    Load properties from cache
    
    Args:
        property_type: Type identifier
        prefer_google_sheets: If True, try Google Sheets first
    
    Returns:
        tuple: (DataFrame, timestamp)
    """
    if prefer_google_sheets:
        # Try loading from Google Sheets first
        try:
            from utils.google_sheets_cache import get_google_sheets_cache
            sheets_cache = get_google_sheets_cache()
            
            if sheets_cache.is_configured():
                df, timestamp = sheets_cache.load_properties(sheet_name=property_type)
                if df is not None:
                    return df, timestamp
        except Exception as e:
            st.warning(f"Failed to load from Google Sheets, trying JSON: {str(e)}")
    
    # Load from JSON (default or fallback)
    filepath = os.path.join(DATA_DIR, f"{property_type}_properties.json")
    
    if not os.path.exists(filepath):
        return None, None
    
    try:
        with open(filepath, 'r') as f:
            cache_data = json.load(f)
        
        df = pd.DataFrame(cache_data["properties"])
        timestamp = cache_data["timestamp"]
        
        return df, timestamp
    except Exception as e:
        print(f"Error loading cache: {e}")
        return None, None

def get_cache_timestamp(property_type="on_market"):
    """Get the timestamp of cached data"""
    filepath = os.path.join(DATA_DIR, f"{property_type}_properties.json")
    
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r') as f:
            cache_data = json.load(f)
        return cache_data.get("timestamp")
    except:
        return None

def format_timestamp(iso_timestamp):
    """Format ISO timestamp to readable string"""
    if not iso_timestamp:
        return "Never"
    
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except:
        return "Unknown"
