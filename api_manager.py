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
                # Using the specialized monthly usage endpoint to get real-time USD
                url = f"https://api.apify.com/v2/users/me/usage/monthly?token={self.apify_key}"
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    # 'totalUsageCreditsUsd' is the actual dollar amount consumed
                    status["apify"]["used"] = data.get('data', {}).get('totalUsageCreditsUsd', 0.0)
            except: 
                pass
        return status

    # ==========================
    # 🏡 ACTIVE LISTINGS
    # ==========================
    def get_active_listings(self, zips, days_back=7):
        """
        Waterfall logic: 
        1. Try Zillow (Cheaper/Faster).
        2. If Zillow yields no valid addresses, try Redfin (Ohio Guarded).
        """
        if not self.apify_key: 
            return pd.DataFrame()

        all_homes = []
        for z in zips:
            homes_found_in_zip = False
            
            # --- ATTEMPT 1: ZILLOW (maxcopell/zillow-zip-search) ---
            try:
                url = f"https://api.apify.com/v2/acts/maxcopell~zillow-zip-search/run-sync-get-dataset-items?token={self.apify_key}"
                payload = {
                    "zipCodes": [str(z)], 
                    "maxItems": 40,
                    "daysOnZillow": str(days_back) # Strict string type required
                }
                res = requests.post(url, json=payload, timeout=120)
                
                if res.status_code in [200, 201]:
                    data = res.json()
                    if isinstance(data, list):
                        for item in data:
                            if not isinstance(item, dict): continue
                            
                            # Multi-field address hunter for reliability
                            street = (
                                item.get('addressStreet') or 
                                item.get('address', {}).get('streetAddress') or 
                                (item.get('address') if isinstance(item.get('address'), str) else None)
                            )
                            
                            if street and len(str(street)) > 5:
                                homes_found_in_zip = True
                                all_homes.append({
                                    "Address": street,
                                    "City": item.get('addressCity') or item.get('address', {}).get('city', 'N/A'),
                                    "Price": item.get('unformattedPrice') or item.get('price', 0),
                                    "Beds": item.get('beds') or item.get('bedrooms'),
                                    "Baths": item.get('baths') or item.get('bathrooms'),
                                    "Source": "Zillow",
                                    "Zip": z,
                                    "URL": item.get('detailUrl') or item.get('url')
                                })
            except: 
                pass

            # --- ATTEMPT 2: REDFIN (benthepythondev/redfin-scraper) ---
            # Triggered if Zillow failed or returned junk/empty
            if not homes_found_in_zip:
                try:
                    url = f"https://api.apify.com/v2/acts/benthepythondev~redfin-scraper/run-sync-get-dataset-items?token={self.apify_key}"
                    # Mandatory State suffix to prevent Florida results
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
                                # Validation: Ensure the listing is actually in the target zip
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
            # Simple Franklin County Logic
            try:
                f_url = "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0/query"
                params = {'where': f"ZIPCD='{zip_code}'", 'outFields': 'SITEADDRESS,OWNERNME1', 'f': 'json', 'resultRecordCount': 20}
                res = requests.get(f_url, params=params, headers=headers, timeout=5)
                if res.status_code == 200:
                    for f in res.json().get('features', []):
                        attr = f['attributes']
                        leads.append({"Address": attr.get('SITEADDRESS'), "Owner": attr.get('OWNERNME1'), "Zip": zip_code, "Source": "Franklin Co"})
            except: 
                pass
        return pd.DataFrame(leads)
