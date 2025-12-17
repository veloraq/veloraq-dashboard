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
                # Use the specialized monthly usage endpoint
                url = f"https://api.apify.com/v2/users/me/usage/monthly?token={self.apify_key}"
                res = requests.get(url)
                if res.status_code == 200:
                    data = res.json()
                    # 'amountAfterVolumeDiscountUsd' is the true dollar amount used
                    status["apify"]["used"] = data.get('data', {}).get('totalUsageCreditsUsd', 0.0)
            except Exception as e:
                print(f"Credit check error: {e}")
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
        """Get market statistics from Parcl Labs API"""
        if not self.parcl_key: 
            return None
        
        headers = {"Authorization": self.parcl_key}
        try:
            # Search for market by zip code
            res = requests.get(
                "https://api.parcllabs.com/v1/search/markets", 
                headers=headers, 
                params={"query": zip_code, "location_type": "ZIP5", "limit": 1}
            )
            if res.status_code != 200: 
                return None
            
            data = res.json()
            items = data.get('items', []) if isinstance(data, dict) else data
            if not items: 
                return None
            
            pid = items[0]['parcl_id']
            
            # Get housing stock data
            res_stats = requests.get(
                f"https://api.parcllabs.com/v1/market_metrics/{pid}/housing_stock", 
                headers=headers
            )
            stock_data = res_stats.json()
            stock_items = stock_data.get('items', []) if isinstance(stock_data, dict) else stock_data
            
            if stock_items:
                latest = stock_items[0]
                total = latest.get('all_properties') or 0
                sf = latest.get('single_family') or 0
                return {
                    'units': total, 
                    'single_family': sf, 
                    'other': total - sf, 
                    'date': latest.get('date')
                }
        except: 
            return None
        return None

    def get_off_market_leads(self, zips):
        """Scrape Franklin and Delaware County auditor websites for off-market leads"""
        leads = []
        headers = {"User-Agent": "Mozilla/5.0"}
        
        for zip_code in zips:
            # FRANKLIN COUNTY
            try:
                f_url = "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0/query"
                queries = [f"ZIPCD='{zip_code}'", f"ZIPCD={zip_code}"]
                found = False
                
                for q in queries:
                    if found: 
                        break
                    try:
                        params = {
                            'where': q, 
                            'outFields': 'SITEADDRESS,OWNERNME1,SALEDATE,ZIPCD', 
                            'f': 'json', 
                            'resultRecordCount': 50
                        }
                        res = requests.get(f_url, params=params, headers=headers, timeout=5)
                        if res.status_code == 200:
                            feats = res.json().get('features', [])
                            if feats: 
                                found = True
                            
                            for f in feats:
                                attr = f['attributes']
                                sold_year = self._parse_date(attr.get('SALEDATE'))
                                
                                # High equity: properties sold before 2015 or legacy properties
                                if (sold_year and sold_year < 2015) or sold_year is None:
                                    leads.append({
                                        "Address": attr.get('SITEADDRESS'),
                                        "Owner": attr.get('OWNERNME1'),
                                        "Zip": attr.get('ZIPCD'),
                                        "Source": "Franklin Co",
                                        "Strategy": f"High Equity ({sold_year or 'Legacy'})"
                                    })
                    except: 
                        pass
            except: 
                pass
            
            # DELAWARE COUNTY
            try:
                d_url = "https://maps.delco-gis.org/arcgiswebadaptor/rest/services/AuditorGISWebsite/AuditorMap_PriorYearParcels_WM/MapServer/0/query"
                params = {
                    'where': f"PROP_ZIP='{zip_code}'", 
                    'outFields': 'PROP_ADDR,OWNER,SALEYEAR', 
                    'f': 'json', 
                    'resultRecordCount': 50
                }
                res = requests.get(d_url, params=params, headers=headers, timeout=10, verify=False)
                if res.status_code == 200:
                    feats = res.json().get('features', [])
                    for f in feats:
                        attr = f['attributes']
                        yr = attr.get('SALEYEAR')
                        
                        # High equity: properties sold before 2015 or legacy properties
                        if yr is None or (str(yr).isdigit() and int(yr) < 2015):
                            leads.append({
                                "Address": attr.get('PROP_ADDR'),
                                "Owner": attr.get('OWNER'),
                                "Zip": zip_code,
                                "Source": "Delaware Co",
                                "Strategy": f"High Equity ({yr or 'Legacy'})"
                            })
            except: 
                pass
        
        return pd.DataFrame(leads)

    def _parse_date(self, date_val):
        """Parse date from various formats"""
        if not date_val: 
            return None
        
        # Unix timestamp (milliseconds)
        if isinstance(date_val, (int, float)) and date_val > 20000000000:
            return datetime.fromtimestamp(date_val / 1000).year
        
        # String date
        if isinstance(date_val, str):
            clean = ''.join(filter(str.isdigit, date_val))
            if len(clean) >= 4:
                return int(clean[:4])
        
        return None
