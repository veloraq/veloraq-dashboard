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

    # ==========================
    # 💳 LIVE CREDIT CHECK (Accurate Dollars)
    # ==========================
    def check_credits(self):
        """Fetches REAL monthly usage from Apify and Parcl APIs."""
        status = {"apify": {"used": 0.0, "limit": 5.0}, "parcl": {"remaining": 0}}
        
        # 1. CHECK APIFY (Monthly Usage Endpoint)
        if self.apify_key:
            try:
                # This endpoint returns true dollar usage for the current cycle
                url = f"https://api.apify.com/v2/users/me/usage/monthly?token={self.apify_key}"
                res = requests.get(url)
                if res.status_code == 200:
                    data = res.json()
                    # Use 'totalUsageCreditsUsd' to match what you see in Apify Console
                    status["apify"]["used"] = data.get('data', {}).get('totalUsageCreditsUsd', 0.0)
            except: pass

        # 2. CHECK PARCL
        if self.parcl_key:
            try:
                url = "https://api.parcllabs.com/v1/search/markets?query=New%20York&location_type=CITY"
                headers = {"Authorization": self.parcl_key}
                res = requests.get(url, headers=headers)
                if res.status_code == 200:
                    status["parcl"]["remaining"] = res.json().get('account', {}).get('est_remaining_credits', 0)
            except: pass
            
        return status

    # ==========================
    # 🏡 ACTIVE LISTINGS (ZILLOW -> REDFIN WATERFALL)
    # ==========================
    def get_active_listings(self, zips, days_back=7):
        """
        Waterfall logic:
        1. Try Zillow (Cheaper/Fast).
        2. If Zillow yields zero valid street addresses, try Redfin (Ohio Guarded).
        """
        if not self.apify_key:
            st.error("❌ Apify Key missing.")
            return pd.DataFrame()

        all_homes = []
        
        for z in zips:
            homes_found_in_zip = False
            
            # --- ATTEMPT 1: ZILLOW ---
            try:
                url = f"https://api.apify.com/v2/acts/maxcopell~zillow-zip-search/run-sync-get-dataset-items?token={self.apify_key}"
                # Zillow Actor strictly requires strings for daysOnZillow
                payload = {
                    "zipCodes": [str(z)], 
                    "maxItems": 40,
                    "
