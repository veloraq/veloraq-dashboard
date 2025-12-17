import requests
import pandas as pd
from datetime import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RealEstateAPI:
    def __init__(self, apify_key=None, parcl_key=None):
        self.apify_key = apify_key
        self.parcl_key = parcl_key

    # ==========================
    # 💳 LIVE CREDIT CHECK
    # ==========================
    def check_credits(self):
        """
        Fetches REAL credit usage from Apify and Parcl APIs.
        """
        status = {"apify": {"used": 0.0, "limit": 5.0}, "parcl": {"remaining": 0}}
        
        # 1. CHECK APIFY (Free Endpoint)
        if self.apify_key:
            try:
                url = f"https://api.apify.com/v2/users/me?token={self.apify_key}"
                res = requests.get(url)
                if res.status_code == 200:
                    data = res.json()
                    limits = data.get('data', {}).get('limits', {})
                    status["apify"]["used"] = limits.get('currentMonthlyUsageUsd', 0.0)
                    status["apify"]["limit"] = limits.get('maxMonthlyUsageUsd', 5.0)
            except: pass

        # 2. CHECK PARCL (Free 'Search' Endpoint)
        if self.parcl_key:
            try:
                # Searching markets is free and returns account balance in header/body
                url = "https://api.parcllabs.com/v1/search/markets?query=New%20York&location_type=CITY"
                headers = {"Authorization": self.parcl_key}
                res = requests.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    # Parcl sends credit info in the 'account' object
                    status["parcl"]["remaining"] = data.get('account', {}).get('est_remaining_credits', 0)
            except: pass
            
        return status

    # ==========================
    # 🏡 SMART LISTINGS (ZILLOW -> REDFIN)
    # ==========================
    def get_active_listings(self, zips, days_back=7):
        if not self.apify_key: return pd.DataFrame()
        all_homes = []
        for z in zips:
            # Try Zillow ($2/1k)
            try:
                listings = self._scrape_zillow(z, days_back)
                if listings:
                    for item in listings: item['Source'] = "Zillow"
                    all_homes.extend(listings)
                    continue 
            except: pass
            
            # Try Redfin ($1/1k)
            try:
                listings = self._scrape_redfin(z)
                if listings:
                    for item in listings: item['Source'] = "Redfin"
                    all_homes.extend(listings)
            except: pass
        return pd.DataFrame(all_homes) if all_homes else pd.DataFrame()

    def _scrape_zillow(self, zip_code, days_back):
        url = f"https://api.apify.com/v2/acts/maxcopell~zillow-zip-search/run-sync-get-dataset-items?token={self.apify_key}"
        res = requests.post(url, json={"zipCode": zip_code, "maxItems": 20, "daysOnZillow": days_back})
        return [{"Address": i.get('address',{}).get('streetAddress'), "Price": i.get('price'), "URL": i.get('url')} for i in res.json()] if res.status_code==201 else []

    def _scrape_redfin(self, zip_code):
        url = f"https://api.apify.com/v2/acts/tri_angle~redfin-search/run-sync-get-dataset-items?token={self.apify_key}"
        res = requests.post(url, json={"location": zip_code, "offerTypes": ["sale"], "maxResultsPerProvider": 20})
        return [{"Address": i.get('address'), "Price": i.get('price'), "URL": i.get('url')} for i in res.json()] if res.status_code==201 else []

    # ==========================
    # 📊 MARKET STATS
    # ==========================
    def get_market_stats(self, zip_code):
        if not self.parcl_key: return None
        headers = {"Authorization": self.parcl_key}
        try:
            res = requests.get("https://api.parcllabs.com/v1/search/markets", headers=headers, params={"query": zip_code, "location_type": "ZIP5", "limit": 1})
            pid = res.json()['items'][0]['parcl_id']
            res_stats = requests.get(f"https://api.parcllabs.com/v1/market_metrics/{pid}/housing_stock", headers=headers)
            latest = res_stats.json()['items'][0]
            total = latest.get('all_properties') or 0
            sf = latest.get('single_family') or 0
            return {'units': total, 'single_family': sf, 'other': total-sf, 'date': latest.get('date')}
        except: return None

    # ==========================
    # 🕵️ OFF-MARKET (COUNTY)
    # ==========================
    def get_off_market_leads(self, zips):
        leads = []
        headers = {"User-Agent": "Mozilla/5.0"}
        for zip_code in zips:
            # Paste the previous County Logic here (Abbreviated for space, keep your full version)
            # Franklin...
            # Delaware...
            pass 
        return pd.DataFrame(leads)
