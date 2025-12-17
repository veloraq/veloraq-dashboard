import requests
import pandas as pd
from datetime import datetime
import urllib3
import streamlit as st

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RealEstateAPI:
    def __init__(self, apify_key=None, parcl_key=None):
        self.apify_key = apify_key
        self.parcl_key = parcl_key

    # ==========================
    # 🏡 SMART LISTINGS (ZILLOW -> REDFIN)
    # ==========================
    def get_active_listings(self, zips, days_back=7):
        """
        Smart Chain: 
        1. Tries Zillow (Cheaper, fast).
        2. If Zillow fails or finds 0 listings, auto-switches to Redfin (More data).
        """
        if not self.apify_key:
            return pd.DataFrame()

        all_homes = []
        
        for z in zips:
            # --- ATTEMPT 1: ZILLOW ($2.00 / 1k results) ---
            try:
                listings = self._scrape_zillow(z, days_back)
                if listings:
                    for item in listings:
                        item['Source'] = "Zillow (Primary)"
                    all_homes.extend(listings)
                    continue # Success! Move to next zip.
            except Exception as e:
                print(f"⚠️ Zillow failed for {z}: {e}")

            # --- ATTEMPT 2: REDFIN ($2.50 / 1k results) ---
            # Triggers only if Zillow returned nothing or crashed
            try:
                print(f"🔄 Switching to Redfin for {z}...")
                listings = self._scrape_redfin(z)
                if listings:
                    for item in listings:
                        item['Source'] = "Redfin (Fallback)"
                    all_homes.extend(listings)
            except Exception as e:
                print(f"❌ Redfin also failed for {z}: {e}")

        if all_homes:
            return pd.DataFrame(all_homes)
        return pd.DataFrame()

    def _scrape_zillow(self, zip_code, days_back):
        # Using 'maxcopell/zillow-zip-search'
        url = f"https://api.apify.com/v2/acts/maxcopell~zillow-zip-search/run-sync-get-dataset-items?token={self.apify_key}"
        payload = {
            "zipCode": zip_code,
            "maxItems": 20, 
            "daysOnZillow": days_back
        }
        res = requests.post(url, json=payload)
        items = []
        if res.status_code == 201:
            for item in res.json():
                items.append({
                    "Address": item.get('address', {}).get('streetAddress', 'N/A'),
                    "City": item.get('address', {}).get('city', 'N/A'),
                    "Price": item.get('price', 0),
                    "Beds": item.get('bedrooms'),
                    "Baths": item.get('bathrooms'),
                    "Zip": zip_code,
                    "URL": item.get('url')
                })
        return items

    def _scrape_redfin(self, zip_code):
        # Using 'tri_angle/redfin-search'
        url = f"https://api.apify.com/v2/acts/tri_angle~redfin-search/run-sync-get-dataset-items?token={self.apify_key}"
        payload = {
            "location": zip_code,
            "offerTypes": ["sale"],
            # Redfin finds EVERYTHING (Land, Multi-Family, Commercial)
            "propertyTypes": ["house", "condo", "land", "multifamily", "commercial"],
            "maxResultsPerProvider": 20
        }
        res = requests.post(url, json=payload)
        items = []
        if res.status_code == 201:
            for item in res.json():
                items.append({
                    "Address": item.get('address', 'N/A'),
                    "City": item.get('city', 'N/A'),
                    "Price": item.get('price', 0),
                    "Beds": item.get('beds'),
                    "Baths": item.get('baths'),
                    "Type": item.get('propertyType', 'Unknown'), # Useful for Land/Comm
                    "Zip": zip_code,
                    "URL": item.get('url')
                })
        return items

    # ==========================
    # 📊 MARKET STATS (PARCL)
    # ==========================
    def get_market_stats(self, zip_code):
        # (Keep your existing Parcl logic here)
        if not self.parcl_key: return None
        headers = {"Authorization": self.parcl_key}
        try:
            res = requests.get("https://api.parcllabs.com/v1/search/markets", headers=headers, params={"query": zip_code, "location_type": "ZIP5", "limit": 1})
            if res.status_code != 200: return None
            data = res.json()
            items = data.get('items', []) if isinstance(data, dict) else data
            if not items: return None
            pid = items[0]['parcl_id']
            
            res_stats = requests.get(f"https://api.parcllabs.com/v1/market_metrics/{pid}/housing_stock", headers=headers)
            stock_data = res_stats.json()
            stock_items = stock_data.get('items', []) if isinstance(stock_data, dict) else stock_data
            
            if stock_items:
                latest = stock_items[0]
                total = latest.get('all_properties') or 0
                sf = latest.get('single_family') or 0
                return {'units': total, 'single_family': sf, 'other': total - sf, 'date': latest.get('date')}
        except: return None
        return None

    # ==========================
    # 🕵️ OFF-MARKET (COUNTY GIS)
    # ==========================
    def get_off_market_leads(self, zips):
        # (Paste your Franklin/Delaware County logic here)
        # Refer to previous messages for the full County GIS block
        return pd.DataFrame()
