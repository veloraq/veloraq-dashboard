import requests
import pandas as pd
import streamlit as st
import credits
from datetime import datetime

# --- HELPER: DATE CONVERTER ---
def parse_county_date(date_val):
    """
    Handles messy dates from County APIs (timestamps, strings, nulls).
    Returns the YEAR (int) or None.
    """
    if not date_val:
        return None
    
    # Case 1: Unix Timestamp (milliseconds) -> e.g. 1104537600000
    if isinstance(date_val, (int, float)):
        # If huge number, assume milliseconds
        if date_val > 20000000000: 
            return datetime.fromtimestamp(date_val / 1000).year
        return None

    # Case 2: String Date -> e.g. "2004-01-01" or "1/1/2004"
    if isinstance(date_val, str):
        # Extract first 4 digits if they look like a year
        cleaned = ''.join(filter(str.isdigit, date_val))
        if len(cleaned) >= 4:
            return int(cleaned[:4])
            
    return None

# --- A. FREE METHOD (County Data - In-Memory Filter) ---
def get_county_leads(zips):
    leads = []
    progress_text = "Scanning County Records..."
    my_bar = st.progress(0, text=progress_text)
    total_steps = len(zips)
    
    for i, zip_code in enumerate(zips):
        my_bar.progress(int((i / total_steps) * 100), text=f"Scanning {zip_code}...")
        
        # 1. FRANKLIN COUNTY
        try:
            f_url = "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0/query"
            
            # STRATEGY CHANGE: Ask for EVERYTHING in the Zip (No Date Filter)
            # We filter in Python below. This avoids API format errors.
            params = {
                'where': f"ZIPCD='{zip_code}'", 
                'outFields': 'SITEADDRESS,OWNERNME1,SALEDATE,ZIPCD', 
                'f': 'json', 
                'resultRecordCount': 50  # Grab 50 records to test
            }
            
            res = requests.get(f_url, params=params, timeout=5)
            
            if res.status_code == 200:
                features = res.json().get('features', [])
                
                for f in features:
                    attr = f['attributes']
                    raw_date = attr.get('SALEDATE')
                    
                    # PYTHON FILTERING (Robust)
                    sold_year = parse_county_date(raw_date)
                    
                    # Logic: If sold before 2015 OR date is missing (Potential Inheritance)
                    if sold_year and sold_year < 2015:
                        leads.append({
                            "Address": attr.get('SITEADDRESS'), 
                            "Owner": attr.get('OWNERNME1'), 
                            "Zip": attr.get('ZIPCD'), 
                            "Source": "Franklin Co",
                            "Last Sale": sold_year
                        })
        except Exception as e:
            print(f"Franklin Error: {e}")

        # 2. DELAWARE COUNTY
        try:
            d_url = "https://maps.delco-gis.org/arcgiswebadaptor/rest/services/AuditorGISWebsite/AuditorMap_PriorYearParcels_WM/MapServer/0/query"
            params = {
                'where': f"PROP_ZIP='{zip_code}'", # No date filter in API
                'outFields': 'PROP_ADDR,OWNER,SALEYEAR', 
                'f': 'json', 
                'resultRecordCount': 50
            }
            res = requests.get(d_url, params=params, timeout=2)
            if res.status_code == 200:
                features = res.json().get('features', [])
                for f in features:
                    attr = f['attributes']
                    raw_year = attr.get('SALEYEAR')
                    
                    # Delaware usually sends simple integers like "1999"
                    if raw_year and int(raw_year) < 2015:
                        leads.append({
                            "Address": attr.get('PROP_ADDR'), 
                            "Owner": attr.get('OWNER'), 
                            "Zip": zip_code, 
                            "Source": "Delaware Co",
                            "Last Sale": raw_year
                        })
        except: pass

    my_bar.empty()
    return pd.DataFrame(leads)

# --- B. PAID METHOD (Parcl - Cleaned Up) ---
def get_parcl_leads(zips, api_key):
    cost = len(zips) * 10
    try:
        credits.spend(cost)
        st.toast(f"💳 Approved: {cost} credits used.")
    except Exception as e:
        st.error(str(e))
        return pd.DataFrame()

    leads = []
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    my_bar = st.progress(0, text="Initializing Parcl...")
    
    for i, zip_code in enumerate(zips):
        my_bar.progress(int((i / len(zips)) * 100), text=f"Querying Parcl for {zip_code}...")
        
        try:
            # 1. GET ID
            res = requests.get("https://api.parcllabs.com/v1/search/markets", headers=headers, params={"query": zip_code, "location_type": "ZIP5", "limit": 1})
            
            if res.status_code != 200: continue
            data = res.json()
            items_list = data.get('items', [])
            if not items_list: continue
            pid = items_list[0]['parcl_id']
            
            # 2. SEARCH PROPERTIES (Corrected V2 Endpoint)
            url = "https://api.parcllabs.com/v2/property_search"
            payload = {"parcl_ids": [pid], "property_filters": {"property_types": ["SINGLE_FAMILY"]}}
            params = {"limit": 10, "offset": 0}
            
            res = requests.post(url, headers=headers, json=payload, params=params)
            
            items = res.json().get('items', [])
            for item in items:
                p = item.get('property_metadata', {})
                address = f"{p.get('address1')}, {p.get('city')}"
                leads.append({
                    "Address": address,
                    "Owner": "Parcl Record",
                    "Zip": zip_code,
                    "Source": "Parcl API",
                    "Year Built": p.get('year_built', 'N/A')
                })
        except: pass

    my_bar.empty()
    return pd.DataFrame(leads)
