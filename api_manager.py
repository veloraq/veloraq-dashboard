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
    # 💳 LIVE CREDIT CHECK
    # ==========================
    def check_credits(self):
        status = {"apify": {"used": 0.0, "limit": 5.0}, "parcl": {"remaining": 0}}
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
    # 🏡 ACTIVE LISTINGS (ZILLOW -> REDFIN FALLBACK)
    # ==========================
    def get_active_listings(self, zips, days_back=7):
        if not self.apify_key:
            st.error("❌ Apify Key is missing.")
            return pd.DataFrame()

        all_homes = []
        
        for z in zips:
            # === ATTEMPT 1: ZILLOW (Primary - Cheaper) ===
            zillow_success = False
            try:
                url = f"https://api.apify.com/v2/acts/maxcopell~zillow-zip-search/run-sync-get-dataset-items?token={self.apify_key}"
                
                # Zillow Payload
                payload = {
                    "zipCodes": [str(z)], 
                    "maxItems": 20,
                    "daysOnZillow": str(days_back)
                }
                
                res = requests.post(url, json=payload, timeout=120)
                
                if res.status_code in [200, 201]:
                    data = res.json()
                    if isinstance(data, list) and len(data) > 0:
                        zillow_success = True
                        for item in data:
                            if isinstance(item, str): continue 
                            all_homes.append({
                                "Address": item.get('address', {}).get('streetAddress', 'N/A'),
                                "City": item.get('address', {}).get('city', 'N/A'),
                                "Price": item.get('price', 0),
                                "Beds": item.get('bedrooms'),
                                "Baths": item.get('bathrooms'),
                                "Source": "Zillow",
                                "Zip": z,
                                "URL": item.get('url')
                            })
            except Exception as e:
                print(f"Zillow Error: {e}")

            # === ATTEMPT 2: REDFIN (Fallback) ===
            # Run this ONLY if Zillow failed or found 0 homes
            if not zillow_success:
                st.toast(f"🔄 Zillow empty for {z}. Trying Redfin...", icon="🔎")
                try:
                    # NEW ACTOR: benthepythondev/redfin-scraper
                    url = f"https://api.apify.com/v2/acts/benthepythondev~redfin-scraper/run-sync-get-dataset-items?token={self.apify_key}"
                    
                    payload = {
                        "location": f"{z}, OH",   # Redfin needs State usually
                        "listingType": "for_sale",
                        "maxItems": 20
                    }
                    
                    # Redfin can be slower, giving it 180s
                    res = requests.post(url, json=payload, timeout=180)
                    
                    if res.status_code in [200, 201]:
                        data = res.json()
                        if isinstance(data, list):
                            for item in data:
                                all_homes.append({
                                    # Redfin output keys are slightly different
                                    "Address": item.get('address', 'N/A'),
                                    "City": item.get('city', 'N/A'),
                                    "Price": item.get('price', 0),
                                    "Beds": item.get('beds'),
                                    "Baths": item.get('baths'),
                                    "Source": "Redfin",
                                    "Zip": z,
                                    "URL": item.get('url')
                                })
                except Exception as e:
                    st.error(f"❌ Redfin Connection Error for {z}: {e}")

        if all_homes:
            return pd.DataFrame(all_homes)
        return pd.DataFrame()

    # ==========================
    # 📊 MARKET STATS
    # ==========================
    def get_market_stats(self, zip_code):
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
                return {'units': total, 'single_family': sf, 'other': total-sf, 'date': latest.get('date')}
        except: return None
        return None

    # ==========================
    # 🕵️ OFF-MARKET (COUNTY)
    # ==========================
    def get_off_market_leads(self, zips):
        leads = []
        headers = {"User-Agent": "Mozilla/5.0"}
        for zip_code in zips:
            # FRANKLIN
            try:
                f_url = "https://gis.franklincountyohio.gov/hosting/rest/services/ParcelFeatures/Parcel_Features/MapServer/0/query"
                queries = [f"ZIPCD='{zip_code}'", f"ZIPCD={zip_code}"]
                found = False
                for q in queries:
                    if found: break
                    try:
                        params = {'where': q, 'outFields': 'SITEADDRESS,OWNERNME1,SALEDATE,ZIPCD', 'f': 'json', 'resultRecordCount': 50}
                        res = requests.get(f_url, params=params, headers=headers, timeout=5)
                        if res.status_code == 200:
                            feats = res.json().get('features', [])
                            if feats: found = True
                            for f in feats:
                                attr = f['attributes']
                                sold_year = self._parse_date(attr.get('SALEDATE'))
                                if (sold_year and sold_year < 2015) or sold_year is None:
                                    leads.append({"Address": attr.get('SITEADDRESS'), "Owner": attr.get('OWNERNME1'), "Zip": attr.get('ZIPCD'), "Source": "Franklin Co", "Strategy": f"High Equity ({sold_year or 'Legacy'})"})
                    except: pass
            except: pass
            
            # DELAWARE
            try:
                d_url = "https://maps.delco-gis.org/arcgiswebadaptor/rest/services/AuditorGISWebsite/AuditorMap_PriorYearParcels_WM/MapServer/0/query"
                params = {'where': f"PROP_ZIP='{zip_code}'", 'outFields': 'PROP_ADDR,OWNER,SALEYEAR', 'f': 'json', 'resultRecordCount': 50}
                res = requests.get(d_url, params=params, headers=headers, timeout=10, verify=False)
                if res.status_code == 200:
                    feats = res.json().get('features', [])
                    for f in feats:
                        attr = f['attributes']
                        yr = attr.get('SALEYEAR')
                        if yr is None or (str(yr).isdigit() and int(yr) < 2015):
                            leads.append({"Address": attr.get('PROP_ADDR'), "Owner": attr.get('OWNER'), "Zip": zip_code, "Source": "Delaware Co", "Strategy": f"High Equity ({yr or 'Legacy'})"})
            except: pass
        return pd.DataFrame(leads)

    def _parse_date(self, date_val):
        if not date_val: return None
        if isinstance(date_val, (int, float)) and date_val > 20000000000: return datetime.fromtimestamp(date_val/1000).year
        if isinstance(date_val, str):
            clean = ''.join(filter(str.isdigit, date_val))
            if len(clean) >= 4: return int(clean[:4])
        return None
