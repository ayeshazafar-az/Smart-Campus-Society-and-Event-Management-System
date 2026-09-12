import os
from supabase import create_client, Client
from dotenv import load_dotenv
import streamlit as st

# Load environment variables (useful for local development)
load_dotenv()

@st.cache_resource
def init_supabase() -> Client:
    """Initialize and return the Supabase client."""
    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        st.error("Supabase credentials not found in environment variables. Please check your .env file.")
        st.stop()
        
    return create_client(url, key)

# Helper function to get the supabase client
def get_supabase() -> Client:
    return init_supabase()
