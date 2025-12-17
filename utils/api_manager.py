import requests
import pandas as pd
from datetime import datetime
import urllib3
import streamlit as st

# Disable SSL warnings for stability
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RealEstateAPI:
    def __init__(self, apify_key=None, parcl_key=None):
        self.apify_key = apify_key
        self.parcl_key = parcl_key

    # ==========================
    # 💳 LIVE CREDIT CHECK
    # ==========================
    def check_credits(self):
        """Fetches REAL monthly usage from Apify."""
        status = {"apify": {"used": 0.0, "limit": 5.0}, "parcl": {"remaining": 0}}
        if self.apify_key:
            try:
                # Specialized endpoint for real-time USD usage
                url = f"https://api.apify.com/v2/users/me/usage/monthly?token={self.apify_key}"
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    status["apify"]["used"] = data.get('data', {}).get('totalUsageCreditsUsd', 0.0)
            except: 
                pass
        return status

    # ==========================
    # 📊 MARKET STATS (Parcl API)
    # ==========================
    def get_market_stats(self, zip_code):
        """Fetches total housing inventory and breakdown."""
        if not self.parcl_key:
            return None
        
        headers = {"Authorization": self.parcl_key}
        try:
            # 1. Search for Parcl Market ID
            search_url = "https://api.parcllabs.com/v1/search/markets"
            params = {"query": zip_code, "location_type": "ZIP5", "limit": 1}
            res = requests.get(search_url, headers=headers, params=params)
            
            if res.status_code == 200:
                items = res.json().get('items', [])
                if not items: return None
                parcl_id = items[0]['parcl_id']
                
                # 2. Get Housing Stock Metrics
                stats_url = f"https://api.parcllabs.com/v1/market_metrics/{parcl_id}/housing_stock"
                res_stats = requests.get(stats_url, headers=headers)
                
                if res_stats.status_code == 200:
                    data = res_stats.json().get('items', [])
                    if data:
                        latest = data[0]
                        return {
                            "total_units": latest.get('all_properties', 0),
                            "single_family": latest.get('single_family', 0),
                            "other": latest.get('all_properties', 0) - latest.get('single_family', 0),
                            "last_updated": latest.get('date', 'N/A')
                        }
        except: 
            pass
        return None

    # ==========================
    # 🏡 ACTIVE LISTINGS (Deep Hunter Waterfall)
    # ==========================
    def get_active_listings(self, zips, days_back=7):
        """
        Waterfall logic: Checks Zillow. If 0 results, forces Redfin fallback.
        Includes Deep Hunter logic for Zillow's 2025 hdpData structure.
        """
        if not self.apify_key: 
            return pd.DataFrame()

        all_homes = []
        for z in zips:
            valid_results_in_zip = 0
            
            # --- ATTEMPT 1: ZILLOW ---
            try:
                url = f"https://api.apify.com/v2/acts/maxcopell~zillow-zip-search/run-sync-get-dataset-items?token={self.apify_key}"
                payload = {
                    "zipCodes": [str(z)], 
                    "maxItems": 40,
                    "daysOnZillow": str(days_back)
                }
                res = requests.post(url, json=payload, timeout=120)
                
                if res.status_code in [200, 201]:
                    data = res.json()
                    if isinstance(data, list) and len(data) > 0:
                        for item in data:
                            if not isinstance(item, dict): continue
                            
                            # 🛡️ 2025 DEEP HUNTER: Hunt in root and hdpData
                            hdp = item.get('hdpData', {}).get('homeInfo', {})
                            street = (
                                item.get('addressStreet') or 
                                hdp.get('streetAddress') or 
                                item.get('address', {}).get('streetAddress')
                            )
                            
                            if street and len(str(street)) > 5:
                                valid_results_in_zip += 1
                                all_homes.append({
                                    "Address": street,
                                    "City": hdp.get('city') or item.get('addressCity') or "N/A",
                                    "Price": hdp.get('price') or item.get('unformattedPrice') or item.get('price', 0),
                                    "Beds": hdp.get('bedrooms') or item.get('beds') or item.get('bedrooms'),
                                    "Baths": hdp.get('bathrooms') or item.get('baths') or item.get('bathrooms'),
                                    "Source": "Zillow",
                                    "Zip": z,
                                    "URL": item.get('detailUrl') or item.get('url')
                                })
            except: 
                pass

            # --- ATTEMPT 2: REDFIN (Forced Fallback if Zillow is 0) ---
            if valid_results_in_zip == 0:
                st.toast(f"🔄 Zillow yield 0 for {z}. Forcing Redfin Ohio...", icon="🔎")
                try:
                    url = f"https://api.apify.com/v2/acts/benthepythondev~redfin-scraper/run-sync-get-dataset-items?token={self.apify_key}"
                    # Guarded location suffix prevents Florida results
                    payload = {"location": f"{z}, OH", "listingType": "for_sale", "maxItems": 20}
                    res = requests.post(url, json=payload, timeout=180)
                    
                    if res.status_code in [200, 201]:
                        data = res.json()
                        if isinstance(data, list):
                            for item in data:
                                api_zip = str(item.get('zip') or item.get('postalCode') or '')
                                if str(z) not in api_zip: continue
                                
                                if item.get('address'):
                                    all_homes.append({
                                        "Address": item.get('address'),
                                        "City": item.get('city', 'N/A'),
                                        "Price": item.get('price', 0),
                                        "Beds": item.get('beds'),
                                        "Baths": item.get('baths'),
                                        "Source": "Redfin",
                                        "Zip": api_zip,
                                        "URL": item.get('url')
                                    })
                except: 
                    pass

        return pd.DataFrame(all_homes)

    # ==========================
    # 🕵️ OFF-MARKET (COUNTY GIS)
    # ==========================
    def get_off_market_leads(self, zips):
        leads = []
        headers = {"User-Agent": "Mozilla/5.0"}
        for zip_code in zips:
            try:
                # Querying Franklin County REST API
                f_url = "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0/query"
                params = {
                    'where': f"ZIPCD='{zip_code}'", 
                    'outFields': 'SITEADDRESS,OWNERNME1', 
                    'f': 'json', 
                    'resultRecordCount': 25
                }
                res = requests.get(f_url, params=params, headers=headers, timeout=10)
                if res.status_code == 200:
                    for f in res.json().get('features', []):
                        attr = f['attributes']
                        leads.append({
                            "Address": attr.get('SITEADDRESS'), 
                            "Owner": attr.get('OWNERNME1'), 
                            "Zip": zip_code, 
                            "Source": "Franklin Co"
                        })
            except: 
                pass
        return pd.DataFrame(leads)
