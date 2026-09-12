import streamlit as st
from utils.db import get_supabase
from dotenv import load_dotenv

# Load config
load_dotenv()

st.set_page_config(
    page_title="Smart Campus Events",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🎓 Smart Campus Society & Event Management")
    st.write("Welcome to the centralized platform for discovering and managing university events.")

    # Initialize Supabase
    supabase = get_supabase()
    
    # Check Auth State (basic placeholder implementation)
    if "user" not in st.session_state:
        st.session_state.user = None
        
    if st.session_state.user is None:
        st.subheader("Please Login or Register to continue.")
        
        # In actual implementation, we will move this to utils/auth.py or separate pages
        tabs = st.tabs(["Login", "Sign Up"])
        
        with tabs[0]:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Log In"):
                try:
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    st.session_state.user = res.user
                    st.success("Successfully logged in!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Login failed: {e}")
                    
        with tabs[1]:
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            name = st.text_input("Full Name", key="signup_name")
            role = st.selectbox("Role", ["student", "society_head", "admin"], key="signup_role")
            
            if st.button("Sign Up"):
                try:
                    res = supabase.auth.sign_up({
                        "email": new_email, 
                        "password": new_password,
                        "options": {
                            "data": {
                                "name": name,
                                "role": role
                            }
                        }
                    })
                    
                    # Guarantee the profile is completely correct using an upsert
                    # This safely overrides any database trigger defaults and avoids metadata parsing bugs
                    if getattr(res, 'user', None):
                        supabase.table("profiles").upsert({
                            "id": res.user.id,
                            "email": new_email,
                            "name": name,
                            "role": role
                        }).execute()
                        
                    st.success("Successfully registered! You can now log in.")
                except Exception as e:
                    st.error(f"Registration failed: {e}")

    else:
        st.success(f"Logged in as {st.session_state.user.email}")
        
        # Route the user to their specific dashboard based on their role
        try:
            profile_res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).execute()
            if profile_res.data:
                role = profile_res.data[0].get("role", "student")
                st.session_state.role = role
                
                if role == "admin":
                    st.switch_page("pages/1_Admin_Dashboard.py")
                elif role == "society_head":
                    st.switch_page("pages/2_Society_Dashboard.py")
                else:
                    st.switch_page("pages/3_Student_Dashboard.py")
        except Exception as e:
            st.error(f"Could not fetch profile: {e}")
            
        if st.button("Log Out"):
            supabase.auth.sign_out()
            st.session_state.user = None
            st.rerun()

if __name__ == "__main__":
    main()