import requests
import pandas as pd
from datetime import datetime
import urllib3
import streamlit as st

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RealEstateAPI:
    def __init__(self, apify_key=None, parcl_key=None, rentcast_key=None):
        self.apify_key = apify_key
        self.parcl_key = parcl_key
        self.rentcast_key = rentcast_key

    def check_credits(self):
        status = {"apify": {"used": 0.0, "limit": 5.0}, "parcl": {"remaining": 0}}
        if self.apify_key:
            try:
                url = f"https://api.apify.com/v2/users/me/usage/monthly?token={self.apify_key}"
                res = requests.get(url)
                if res.status_code == 200:
                    data = res.json()
                    status["apify"]["used"] = data.get('data', {}).get('totalUsageCreditsUsd', 0.0)
            except:
                pass
        return status

    def get_active_listings(self, zips, days_back=7):
        if not self.apify_key:
            return pd.DataFrame()

        all_homes = []
        for z in zips:
            homes_found_in_zip = False
            
            # --- ZILLOW ATTEMPT ---
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
                    if isinstance(data, list):
                        for item in data:
                            if not isinstance(item, dict): continue
                            street = item.get('addressStreet') or item.get('address', {}).get('streetAddress')
                            if street:
                                homes_found_in_zip = True
                                all_homes.append({
                                    "Address": street,
                                    "City": item.get('addressCity') or "N/A",
                                    "Price": item.get('price', 0),
                                    "Source": "Zillow",
                                    "Zip": z,
                                    "URL": item.get('detailUrl') or item.get('url')
                                })
            except:
                pass

            # --- REDFIN FALLBACK ---
            if not homes_found_in_zip:
                try:
                    url = f"https://api.apify.com/v2/acts/benthepythondev~redfin-scraper/run-sync-get-dataset-items?token={self.apify_key}"
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
                                        "Source": "Redfin",
                                        "Zip": api_zip,
                                        "URL": item.get('url')
                                    })
                except:
                    pass

        return pd.DataFrame(all_homes)

    def get_market_stats(self, zip_code):
        return None # Simplified for syntax stability

    def get_off_market_leads(self, zips):
        return pd.DataFrame() # Simplified for syntax stability
