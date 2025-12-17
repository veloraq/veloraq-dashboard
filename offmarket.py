import requests
import pandas as pd
import streamlit as st
import credits
from datetime import datetime
import urllib3

# Disable SSL warnings for government sites (crucial for Delaware/older servers)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- HELPER: DATE CONVERTER ---
def parse_county_date(date_val):
    """
    Parses messy dates from county records.
    Returns the YEAR (int) or None.
    """
    if not date_val:
        return None
    
    # Case 1: Unix Timestamp (milliseconds)
    if isinstance(date_val, (int, float)):
        if date_val > 20000000000: 
            return datetime.fromtimestamp(date_val / 1000).year
        return None

    # Case 2: String Date -> "2004-01-01" or "1999"
    if isinstance(date_val, str):
        cleaned = ''.join(filter(str.isdigit, date_val))
        if len(cleaned) >= 4:
            return int(cleaned[:4])
    return None

# --- A. FREE METHOD (County Data) ---
def get_county_leads(zips):
    leads = []
    
    # Progress Bar Setup
    progress_text = "Scanning County Records..."
    my_bar = st.progress(0, text=progress_text)
    status_area = st.empty()
    total_steps = len(zips)
    
    # 🛡️ DISGUISE HEADERS (Crucial for Delaware/Government servers)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    for i, zip_code in enumerate(zips):
        my_bar.progress(int((i / total_steps) * 100), text=f"Scanning {zip_code}...")
        
        # 1. FRANKLIN COUNTY
        # LOGIC: Try Zip as String ('43081') AND as Number (43081)
        f_url = "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0/query"
        queries = [f"ZIPCD='{zip_code}'", f"ZIPCD={zip_code}"]
        found_franklin = False
        
        for q in queries:
            if found_franklin: break
            try:
                # Retrieve ALL records for Zip (filtering happens in Python below)
                params = {
                    'where': q, 
                    'outFields': 'SITEADDRESS,OWNERNME1,SALEDATE,ZIPCD', 
                    'f': 'json', 
                    'resultRecordCount': 50 
                }
                res = requests.get(f_url, params=params, headers=headers, timeout=5)
                
                if res.status_code == 200:
                    features = res.json().get('features', [])
                    if not features: continue
                    
                    found_franklin = True
                    status_area.text(f"✅ Franklin: Found {len(features)} records. Filtering...")
                    
                    for f in features:
                        attr = f['attributes']
                        sold_year = parse_county_date(attr.get('SALEDATE'))
                        
                        # STRATEGY: Keep if < 2015 OR Date is Missing (Legacy)
                        strategy = "Unknown"
                        keep = False
                        if sold_year and sold_year < 2015:
                            strategy = f"High Equity ({sold_year})"
                            keep = True
                        elif sold_year is None:
                            strategy = "Legacy Owner (No Date)"
                            keep = True
                            
                        if keep:
                            leads.append({
                                "Address": attr.get('SITEADDRESS'), 
                                "Owner": attr.get('OWNERNME1'), 
                                "Zip": attr.get('ZIPCD'), 
                                "Source": "Franklin Co",
                                "Strategy": strategy
                            })
            except Exception as e:
                print(f"Franklin Error: {e}")

        # 2. DELAWARE COUNTY
        try:
            d_url = "https://maps.delco-gis.org/arcgiswebadaptor/rest/services/AuditorGISWebsite/AuditorMap_PriorYearParcels_WM/MapServer/0/query"
            
            # Simplified query (Zip only) + Verify=False to bypass SSL errors
            params = {
                'where': f"PROP_ZIP='{zip_code}'", 
                'outFields': 'PROP_ADDR,OWNER,SALEYEAR', 
                'f': 'json', 
                'resultRecordCount': 50
            }
            
            res = requests.get(d_url, params=params, headers=headers, timeout=10, verify=False)
            
            if res.status_code == 200:
                features = res.json().get('features', [])
                if features:
                    status_area.text(f"✅ Delaware: Found {len(features)} records.")
                
                for f in features:
                    attr = f['attributes']
                    raw_year = attr.get('SALEYEAR')
                    
                    keep = False
                    strategy = "Unknown"
                    
                    if raw_year is None:
                        keep = True
                        strategy = "Legacy Owner (No Date)"
                    elif str(raw_year).isdigit() and int(raw_year) < 2015:
                        keep = True
                        strategy = f"High Equity ({raw_year})"
                        
                    if keep:
                        leads.append({
                            "Address": attr.get('PROP_ADDR'), 
                            "Owner": attr.get('OWNER'), 
                            "Zip": zip_code, 
                            "Source": "Delaware Co",
                            "Strategy": strategy
                        })
        except Exception as e:
            print(f"Delaware Error: {e}")

    my_bar.empty()
    status_area.empty()
    return pd.DataFrame(leads)

# --- B. PAID METHOD (Parcl Database) ---
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
            
            if res.status_code != 200: continue

            items = res.json().get('items', [])
            for item in items:
                p = item.get('property_metadata', {})
                address = f"{p.get('address1')}, {p.get('city')}"
                leads.append({
                    "Address": address,
                    "Owner": "Parcl Record",
                    "Zip": zip_code,
                    "Source": "Parcl API",
                    "Strategy": "Market Search"
                })
        except: pass

    my_bar.empty()
    return pd.DataFrame(leads)
