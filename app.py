import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
from pages import home, off_market, on_market, analysis
from utils.api_manager import RealEstateAPI

# Page configuration
st.set_page_config(
    page_title="Columbus RE Investor - Real Estate Investment Tool",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    .property-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        font-size: 0.875rem;
        font-weight: 500;
        margin-right: 0.5rem;
    }
    .badge-warning { background-color: #fff3cd; color: #856404; }
    .badge-danger { background-color: #f8d7da; color: #721c24; }
    .badge-success { background-color: #d4edda; color: #155724; }
    .badge-info { background-color: #d1ecf1; color: #0c5460; }
</style>
""", unsafe_allow_html=True)

# Initialize session state for API keys
if 'api_keys_configured' not in st.session_state:
    st.session_state.api_keys_configured = False

# Sidebar - API Configuration
with st.sidebar.expander("⚙️ API Configuration", expanded=not st.session_state.api_keys_configured):
    st.markdown("### API Keys")
    st.markdown("Configure your API keys to fetch live data")
    
    apify_key = st.text_input(
        "Apify API Key", 
        type="password", 
        value=st.session_state.get('apify_key', ''),
        help="Get your API key from apify.com"
    )
    
    parcl_key = st.text_input(
        "Parcl Labs API Key (Optional)", 
        type="password", 
        value=st.session_state.get('parcl_key', ''),
        help="Get your API key from parcllabs.com for market stats"
    )
    
    if apify_key:
        st.session_state.apify_key = apify_key
        st.session_state.api_keys_configured = True
        
        # Create API manager instance
        api_manager = RealEstateAPI(
            apify_key=apify_key,
            parcl_key=parcl_key if parcl_key else None
        )
        st.session_state.api_manager = api_manager
        
        # Check credits
        try:
            credits = api_manager.check_credits()
            st.success(f"✓ Apify configured - ${credits['apify']['used']:.2f} / ${credits['apify']['limit']:.2f} used")
            
            if parcl_key:
                st.success("✓ Parcl Labs configured")
        except:
            st.success("✓ Apify configured")
    else:
        st.info("Add API key to fetch live data, or use demo data")

# Sidebar navigation
st.sidebar.title("🏢 Columbus RE Investor")
page = st.sidebar.radio(
    "Navigation",
    ["Home", "Off-Market Listings", "On-Market Listings", "Investment Analysis"]
)

# Route to appropriate page
if page == "Home":
    home.show()
elif page == "Off-Market Listings":
    off_market.show()
elif page == "On-Market Listings":
    on_market.show()
elif page == "Investment Analysis":
    analysis.show()
