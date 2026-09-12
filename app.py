import os
import streamlit as st
from utils.db import get_supabase, reset_supabase_session
from utils.ui import apply_custom_theme, render_html
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="CampusPulse · Smart Campus OS",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def main():
    apply_custom_theme()
    supabase = get_supabase()

    if "user" not in st.session_state:
        st.session_state.user = None

    # Redirect immediately if already logged in
    if st.session_state.user is not None:
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
            st.error(f"Error loading session profile: {e}")
            if st.button("Reset Session"):
                reset_supabase_session()
                st.session_state.user = None
                st.rerun()
        return

    # ==========================================
    # SPLIT-SCREEN LANDING & AUTH
    # ==========================================
    col_hero, col_spacer, col_auth = st.columns([6, 0.5, 5])

    with col_hero:
        render_html("""
        <div style="padding-top: 1rem; animation: fadeInUp 0.6s ease both;">
            
            <div style="display: inline-flex; align-items: center; gap: 0.5rem; background: rgba(129, 140, 248, 0.1); border: 1px solid rgba(129, 140, 248, 0.2); padding: 0.35rem 0.9rem; border-radius: 999px; margin-bottom: 1.75rem;">
                <span style="display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #818cf8; box-shadow: 0 0 8px #818cf8;"></span>
                <span style="font-size: 0.725rem; font-weight: 700; color: #818cf8; text-transform: uppercase; letter-spacing: 0.08em;">Campus Event OS</span>
            </div>
            
            <h1 style="font-size: 2.85rem; font-weight: 800; color: #f1f5f9; line-height: 1.15; letter-spacing: -0.04em; margin: 0 0 1.25rem 0;">
                The central<br>
                <span style="background: linear-gradient(135deg, #667eea, #764ba2, #22d3ee); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;">operating system</span><br>
                for university life.
            </h1>
            
            <p style="font-size: 1.05rem; color: #94a3b8; line-height: 1.7; margin-bottom: 2rem; max-width: 520px;">
                Discover verified campus societies, book real-time event passes with secure QR tokens, and get personalized AI recommendations.
            </p>
            
            <div style="display: flex; flex-direction: column; gap: 0.85rem; margin-bottom: 2rem;">
                
                <div class="glass-card" style="padding: 1rem 1.25rem; margin-bottom: 0;">
                    <div style="display: flex; align-items: center; gap: 0.85rem;">
                        <div style="width: 42px; height: 42px; border-radius: 12px; background: rgba(129, 140, 248, 0.12); border: 1px solid rgba(129, 140, 248, 0.2); color: #818cf8; display: flex; align-items: center; justify-content: center; font-size: 1.15rem; flex-shrink: 0;">🏛️</div>
                        <div>
                            <div style="font-size: 0.9rem; font-weight: 700; color: #f1f5f9; margin-bottom: 0.15rem;">Verified Society Governance</div>
                            <div style="font-size: 0.8rem; color: #64748b; line-height: 1.4;">Official approval pipelines and admin moderation for campus organizations.</div>
                        </div>
                    </div>
                </div>
                
                <div class="glass-card" style="padding: 1rem 1.25rem; margin-bottom: 0;">
                    <div style="display: flex; align-items: center; gap: 0.85rem;">
                        <div style="width: 42px; height: 42px; border-radius: 12px; background: rgba(52, 211, 153, 0.12); border: 1px solid rgba(52, 211, 153, 0.2); color: #34d399; display: flex; align-items: center; justify-content: center; font-size: 1.15rem; flex-shrink: 0;">🎫</div>
                        <div>
                            <div style="font-size: 0.9rem; font-weight: 700; color: #f1f5f9; margin-bottom: 0.15rem;">Digital QR Event Passes</div>
                            <div style="font-size: 0.8rem; color: #64748b; line-height: 1.4;">Instant QR ticket generation with capacity enforcement and duplicate-proof check-ins.</div>
                        </div>
                    </div>
                </div>
                
                <div class="glass-card" style="padding: 1rem 1.25rem; margin-bottom: 0;">
                    <div style="display: flex; align-items: center; gap: 0.85rem;">
                        <div style="width: 42px; height: 42px; border-radius: 12px; background: rgba(167, 139, 250, 0.12); border: 1px solid rgba(167, 139, 250, 0.2); color: #a78bfa; display: flex; align-items: center; justify-content: center; font-size: 1.15rem; flex-shrink: 0;">✨</div>
                        <div>
                            <div style="font-size: 0.9rem; font-weight: 700; color: #f1f5f9; margin-bottom: 0.15rem;">Gemini AI Campus Intelligence</div>
                            <div style="font-size: 0.8rem; color: #64748b; line-height: 1.4;">Contextual event recommendations matching your major and activity history.</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div style="display: flex; align-items: center; gap: 1.5rem; font-size: 0.775rem; font-weight: 600; color: #475569;">
                <span style="display: flex; align-items: center; gap: 0.35rem;"><span style="color: #34d399;">●</span> Role-Based Access</span>
                <span style="display: flex; align-items: center; gap: 0.35rem;"><span style="color: #818cf8;">●</span> Supabase Powered</span>
                <span style="display: flex; align-items: center; gap: 0.35rem;"><span style="color: #a78bfa;">●</span> University Verified</span>
            </div>
        </div>
        """)

    with col_auth:
        render_html("<div style='height: 1rem;'></div>")
        
        with st.container(border=True):
            render_html("""
            <div style="margin-bottom: 1.25rem;">
                <div style="display: inline-flex; align-items: center; justify-content: center; width: 48px; height: 48px; border-radius: 14px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; font-weight: 800; font-size: 1.3rem; margin-bottom: 0.85rem; box-shadow: 0 4px 16px rgba(102, 126, 234, 0.35); animation: pulseGlow 3s ease infinite;">C</div>
                <h2 style="font-size: 1.5rem; font-weight: 800; color: #f1f5f9; margin: 0; letter-spacing: -0.03em;">Welcome to CampusPulse</h2>
                <p style="font-size: 0.875rem; color: #64748b; margin-top: 0.3rem;">Sign in to your university portal or create an account.</p>
            </div>
            """)

            tabs = st.tabs(["Sign In", "Create Account"])

            with tabs[0]:
                email = st.text_input("University Email", placeholder="student@campus.edu", key="login_email")
                password = st.text_input("Password", type="password", placeholder="••••••••", key="login_password")
                
                render_html("<div style='height: 8px;'></div>")
                if st.button("Sign In to Portal", type="primary", use_container_width=True):
                    if not email.strip() or not password.strip():
                        st.error("Please enter both email and password.")
                    else:
                        try:
                            res = supabase.auth.sign_in_with_password({"email": email.strip(), "password": password.strip()})
                            st.session_state.user = res.user
                            st.success("Authentication successful! Redirecting...")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Sign in failed: {e}")

            with tabs[1]:
                name = st.text_input("Full Name", placeholder="Alex Morgan", key="signup_name")
                new_email = st.text_input("Email Address", placeholder="name@campus.edu", key="signup_email")
                new_password = st.text_input("Create Password", type="password", placeholder="Minimum 6 characters", key="signup_password")
                
                role_choice = st.selectbox(
                    "Account Type",
                    ["Student", "Society Head", "Administrator"],
                    key="signup_role_choice",
                    help="Select your university designation."
                )
                
                admin_key_input = ""
                if role_choice == "Administrator":
                    admin_key_input = st.text_input(
                        "Administrator Authorization Key*", 
                        type="password", 
                        key="admin_key_input", 
                        placeholder="Enter authorization key",
                        help="Required secret key to provision administrative privileges."
                    )
                
                role = "admin" if role_choice == "Administrator" else ("society_head" if role_choice == "Society Head" else "student")
                
                render_html("<div style='height: 8px;'></div>")
                if st.button("Create Account", type="primary", use_container_width=True):
                    is_admin_attempt = (role_choice == "Administrator")
                    
                    if not name.strip():
                        st.error("Please enter your full name.")
                    elif not new_email.strip() or "@" not in new_email:
                        st.error("Please provide a valid email address.")
                    elif len(new_password) < 6:
                        st.error("Password must be at least 6 characters long.")
                    elif is_admin_attempt and admin_key_input.strip() != os.environ.get("ADMIN_SECRET_KEY", "campus_admin_2026"):
                        st.error("Invalid Administrator Authorization Key. Registration denied.")
                    else:
                        target_role = "admin" if is_admin_attempt else role
                        try:
                            res = supabase.auth.sign_up({
                                "email": new_email.strip(),
                                "password": new_password.strip(),
                                "options": {
                                    "data": {
                                        "name": name.strip(),
                                        "role": target_role
                                    }
                                }
                            })
                            
                            # Upsert profile record
                            if getattr(res, 'user', None):
                                supabase.table("profiles").upsert({
                                    "id": res.user.id,
                                    "email": new_email.strip(),
                                    "name": name.strip(),
                                    "role": target_role
                                }).execute()
                                
                            st.success("Account created successfully! You can now sign in.")
                        except Exception as e:
                            st.error(f"Registration failed: {e}")

if __name__ == "__main__":
    main()