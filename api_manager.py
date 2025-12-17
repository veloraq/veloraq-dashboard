import requests
import pandas as pd
from datetime import datetime
import urllib3

# Disable SSL warnings for County sites
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RealEstateAPI:
    def __init__(self, apify_key=None, parcl_key=None):
        self.apify_key = apify_key
        self.parcl_key = parcl_key
        self.headers = {"Content-Type": "application/json"}

    # ==========================
    # 🏡 ACTIVE LISTINGS (APIFY)
    # ==========================
    def get_active_listings(self, zips, days_back=7):
        """
        Fetches listings using Apify (Realtor.com Scraper).
        Falls back to empty DataFrame if no key provided.
        """
        if not self.apify_key:
            return pd.DataFrame()

        all_homes = []
        
        # Endpoint: Run Actor Synchronously & Get Items
        # We use the 'epctex/realtor-scraper' actor
        url = f"https://api.apify.com/v2/acts/epctex~realtor-scraper/run-sync-get-dataset-items?token={self.apify_key}"
        
        for z in zips:
            try:
                # Payload: Configures the scraper
                payload = {
                    "search": z,
                    "limit": 20,           # Keep it fast/cheap
                    "type": "sale",        # For Sale
                    "sort": "newest",      # Get recent stuff
                    "days_on_market": days_back
                }
                
                res = requests.post(url, json=payload)
                
                if res.status_code == 201: # 201 = Created & Finished
                    data = res.json()
                    
                    for item in data:
                        # Normalize Apify Data to our Standard Format
                        all_homes.append({
                            "Address": item.get('address', {}).get('line', 'N/A'),
                            "City": item.get('address', {}).get('city', 'N/A'),
                            "Price": item.get('list_price', 0),
                            "Days on Market": days_back, # Approximate or parse from listing
                            "Source": "Apify (Realtor)",
                            "Zip": z,
                            "URL": item.get('href')
                        })
                else:
                    print(f"Apify Error {res.status_code}: {res.text}")
                    
            except Exception as e:
                print(f"Connection Error on {z}: {e}")
        
        if all_homes:
            return pd.DataFrame(all_homes)
        return pd.DataFrame()

    # ==========================
    # 📊 MARKET STATS (PARCL)
    # ==========================
    def get_market_stats(self, zip_code):
        if not self.parcl_key: return None
        
        headers = {"Authorization": self.parcl_key}
        try:
            # 1. Get ID
            res = requests.get("https://api.parcllabs.com/v1/search/markets", headers=headers, params={"query": zip_code, "location_type": "ZIP5", "limit": 1})
            if res.status_code != 200: return None
            data = res.json()
            items = data.get('items', []) if isinstance(data, dict) else data
            if not items: return None
            pid = items[0]['parcl_id']
            
            # 2. Get Stats
            res_stats = requests.get(f"https://api.parcllabs.com/v1/market_metrics/{pid}/housing_stock", headers=headers)
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
        except: return None
        return None

    # ==========================
    # 🕵️ OFF-MARKET (COUNTY GIS)
    # ==========================
    def get_off_market_leads(self, zips):
        """
        Directly implements the Franklin/Delaware logic here.
        This keeps offmarket.py purely for display.
        """
        leads = []
        headers = {"User-Agent": "Mozilla/5.0"} # Disguise
        
        for zip_code in zips:
            # 1. FRANKLIN
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
                                    leads.append({
                                        "Address": attr.get('SITEADDRESS'),
                                        "Owner": attr.get('OWNERNME1'),
                                        "Zip": attr.get('ZIPCD'),
                                        "Source": "Franklin Co",
                                        "Strategy": f"High Equity ({sold_year or 'Legacy'})"
                                    })
                    except: pass
            except: pass

            # 2. DELAWARE
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
                            leads.append({
                                "Address": attr.get('PROP_ADDR'),
                                "Owner": attr.get('OWNER'),
                                "Zip": zip_code,
                                "Source": "Delaware Co",
                                "Strategy": f"High Equity ({yr or 'Legacy'})"
                            })
            except: pass
            
        return pd.DataFrame(leads)

    def _parse_date(self, date_val):
        if not date_val: return None
        if isinstance(date_val, (int, float)) and date_val > 20000000000:
            return datetime.fromtimestamp(date_val/1000).year
        if isinstance(date_val, str):
            clean = ''.join(filter(str.isdigit, date_val))
            if len(clean) >= 4: return int(clean[:4])
        return None
