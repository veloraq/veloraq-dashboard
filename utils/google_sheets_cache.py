import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json

class GoogleSheetsCache:
    def __init__(self, credentials_json=None):
        """
        Initialize Google Sheets API client
        
        Args:
            credentials_json: Google service account credentials as JSON string or dict
        """
        self.service = None
        self.spreadsheet_id = None
        
        if credentials_json:
            try:
                # Parse credentials if string
                if isinstance(credentials_json, str):
                    creds_dict = json.loads(credentials_json)
                else:
                    creds_dict = credentials_json
                
                # Create credentials
                credentials = service_account.Credentials.from_service_account_info(
                    creds_dict,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                
                # Build service
                self.service = build('sheets', 'v4', credentials=credentials)
                
            except Exception as e:
                st.error(f"Failed to initialize Google Sheets: {str(e)}")
    
    def set_spreadsheet_id(self, spreadsheet_id):
        """Set the Google Sheets spreadsheet ID"""
        self.spreadsheet_id = spreadsheet_id
    
    def is_configured(self):
        """Check if Google Sheets is properly configured"""
        return self.service is not None and self.spreadsheet_id is not None
    
    def save_properties(self, df, sheet_name="on_market", mode="overwrite"):
        """
        Save properties DataFrame to Google Sheets
        
        Args:
            df: pandas DataFrame with property data
            sheet_name: Name of the sheet tab
            mode: "overwrite" or "append" for incremental updates
        """
        if not self.is_configured():
            raise Exception("Google Sheets not configured")
        
        try:
            # Add timestamp column
            df_copy = df.copy()
            df_copy['last_updated'] = datetime.now().isoformat()
            
            # Convert DataFrame to list of lists
            values = [df_copy.columns.tolist()] + df_copy.values.tolist()
            
            if mode == "append":
                # Append new data
                body = {'values': values[1:]}  # Skip header
                self.service.spreadsheets().values().append(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{sheet_name}!A:Z",
                    valueInputOption='RAW',
                    body=body
                ).execute()
            else:
                # Overwrite existing data
                body = {'values': values}
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.spreadsheet_id,
                    range=f"{sheet_name}!A1",
                    valueInputOption='RAW',
                    body=body
                ).execute()
            
            return datetime.now().isoformat()
            
        except HttpError as e:
            st.error(f"Google Sheets API error: {str(e)}")
            raise
    
    def load_properties(self, sheet_name="on_market"):
        """
        Load properties from Google Sheets
        
        Args:
            sheet_name: Name of the sheet tab to read from
            
        Returns:
            tuple: (DataFrame, timestamp)
        """
        if not self.is_configured():
            raise Exception("Google Sheets not configured")
        
        try:
            # Read data from sheet
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:Z"
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return None, None
            
            # Convert to DataFrame
            df = pd.DataFrame(values[1:], columns=values[0])
            
            # Get timestamp from last_updated column if it exists
            timestamp = None
            if 'last_updated' in df.columns:
                timestamp = df['last_updated'].iloc[-1] if len(df) > 0 else None
                df = df.drop('last_updated', axis=1)
            
            return df, timestamp
            
        except HttpError as e:
            st.error(f"Google Sheets API error: {str(e)}")
            return None, None
    
    def create_sheet_if_not_exists(self, sheet_name):
        """Create a new sheet tab if it doesn't exist"""
        if not self.is_configured():
            raise Exception("Google Sheets not configured")
        
        try:
            # Get existing sheets
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            sheet_names = [sheet['properties']['title'] 
                          for sheet in spreadsheet['sheets']]
            
            # Create sheet if it doesn't exist
            if sheet_name not in sheet_names:
                body = {
                    'requests': [{
                        'addSheet': {
                            'properties': {
                                'title': sheet_name
                            }
                        }
                    }]
                }
                self.service.spreadsheets().batchUpdate(
                    spreadsheetId=self.spreadsheet_id,
                    body=body
                ).execute()
                
        except HttpError as e:
            st.error(f"Error creating sheet: {str(e)}")

def get_google_sheets_cache():
    """Get or create Google Sheets cache instance from session state"""
    if 'google_sheets_cache' not in st.session_state:
        # Try to load credentials from secrets
        credentials = None
        if hasattr(st, 'secrets') and 'GOOGLE_SHEETS_CREDENTIALS' in st.secrets:
            credentials = st.secrets['GOOGLE_SHEETS_CREDENTIALS']
        
        st.session_state.google_sheets_cache = GoogleSheetsCache(credentials)
    
    return st.session_state.google_sheets_cache
