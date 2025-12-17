import requests
import pandas as pd
from datetime import datetime
import urllib3
import streamlit as st

# Disable SSL warnings for cleaner logs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RealEstateAPI:
    def __init__(self, apify_key=None, parcl_key=None):
        self.apify_key = apify_key
        self.parcl_key = parcl_key

    # ==========================
    # 💳 LIVE CREDIT CHECK
    # ==========================
    def check_credits(self):
        """Fetches accurate monthly usage from Apify."""
        status = {"apify": {"used": 0.0, "limit": 5.0}, "parcl": {"remaining": 0}}
        if self.apify_key:
            try:
                # Specialized endpoint for real-time dollar amounts
                url = f"https://api.apify.com/v2/users/me/usage/monthly?token={self.apify_key}"
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    status["apify"]["used"] = data.get('data', {}).get('totalUsageCreditsUsd', 0.0)
            except: 
                pass
        return status

    # ==========================
    # 🏡 ACTIVE LISTINGS (Waterfall logic)
    # ==========================
    def get_active_listings(self, zips, days_back=7):
        """
        Waterfall logic: 
        Checks Zillow first. If it yields 0 actual street addresses, 
        it triggers a Redfin scan as a fallback.
        """
        if not self.apify_key: 
            return pd.DataFrame()

        all_homes = []
        
        for z in zips:
            # results_count tracks ACTUAL homes, not just API success
            results_count = 0 
            
            # --- ATTEMPT 1: ZILLOW (Primary) ---
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
                            
                            # DEEP HUNTER: Hunt for address in all possible Zillow keys
                            street = (
                                item.get('addressStreet') or 
                                item.get('address', {}).get('streetAddress') or
                                item.get('hdpData', {}).get('homeInfo', {}).get('streetAddress')
                            )
                            
                            if street and len(str(street)) > 5:
                                results_count += 1
                                all_homes.append({
                                    "Address": street,
                                    "City": item.get('addressCity') or item.get('hdpData', {}).get('homeInfo', {}).get('city', 'N/A'),
                                    "Price": item.get('unformattedPrice') or item.get('price', 0),
                                    "Beds": item.get('beds') or item.get('bedrooms') or item.get('hdpData', {}).get('homeInfo', {}).get('bedrooms'),
                                    "Baths": item.get('baths') or item.get('bathrooms') or item.get('hdpData', {}).get('homeInfo', {}).get('bathrooms'),
                                    "Source": "Zillow",
                                    "Zip": z,
                                    "URL": item.get('detailUrl') or item.get('url')
                                })
            except: 
                pass

            # --- ATTEMPT 2: REDFIN (Forced Fallback Notification) ---
            if results_count == 0:
                # UI Notification for the User
                st.toast(f"🔎 No Zillow data for {z}. Switching to Redfin...", icon="🔄")
                
                try:
                    url = f"https://api.apify.com/v2/acts/benthepythondev~redfin-scraper/run-sync-get-dataset-items?token={self.apify_key}"
                    payload = {
                        "location": f"{z}, OH", 
                        "listingType": "for_sale",
                        "maxItems": 20
                    }
                    res = requests.post(url, json=payload, timeout=180)
                    
                    if res.status_code in [200, 201]:
                        data = res.json()
                        if isinstance(data, list):
                            for item in data:
                                # Ohio Guard: Validation to prevent Florida default
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
    # 🕵️ OFF-MARKET (COUNTY)
    # ==========================
    def get_off_market_leads(self, zips):
        leads = []
        headers = {"User-Agent": "Mozilla/5.0"}
        for zip_code in zips:
            try:
                # Franklin County GIS
                f_url = "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0/query"
                params = {'where': f"ZIPCD='{zip_code}'", 'outFields': 'SITEADDRESS,OWNERNME1', 'f': 'json', 'resultRecordCount': 20}
                res = requests.get(f_url, params=params, headers=headers, timeout=5)
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
