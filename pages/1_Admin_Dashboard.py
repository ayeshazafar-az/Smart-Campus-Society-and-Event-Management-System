import streamlit as st
import pandas as pd
from utils.db import get_supabase, reset_supabase_session
from utils.ui import (
    apply_custom_theme, 
    render_app_bar, 
    render_page_header, 
    render_kpi_card, 
    render_empty_state,
    render_html
)

st.set_page_config(page_title="Administration · CampusPulse", page_icon="⚙️", layout="wide")

def check_admin():
    apply_custom_theme()
    
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("Please sign in from the main portal to access the administration console.")
        if st.button("Return to Sign In", type="primary"):
            st.switch_page("app.py")
        st.stop()
        
    supabase = get_supabase()
    try:
        res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).execute()
        if not res.data:
            st.error("Profile not found in database.")
            st.stop()
        profile = res.data[0]
        if str(profile.get("role")).strip().lower() != "admin":
            st.error("Access Denied: University Administrator privileges required.")
            if st.button("Return to Home"):
                st.switch_page("app.py")
            st.stop()
        return profile, supabase
    except Exception as e:
        st.error(f"Database Error: {str(e)}")
        st.stop()

admin_profile, supabase = check_admin()

# App Bar with integrated logout
if render_app_bar(user_email=st.session_state.user.email, user_role="admin", user_name=admin_profile.get("name")):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.user = None
    st.session_state.role = None
    reset_supabase_session()
    st.switch_page("app.py")

# Page Header
render_page_header(
    tag="Administration Console",
    title="University Oversight & Moderation",
    description="Monitor platform engagement, review pending society charters, and authorize event proposals."
)

# Fetch Platform-Wide Metrics
stu_res = supabase.table("profiles").select("id", count="exact").eq("role", "student").execute()
soc_res = supabase.table("societies").select("id", count="exact").execute()
evt_res = supabase.table("events").select("id", count="exact").execute()
reg_total = supabase.table("registrations").select("id", count="exact").execute()

# KPI Metric Cards Row
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card("Total Students", stu_res.count or 0, "Registered accounts", "🎓")
with c2:
    render_kpi_card("Campus Societies", soc_res.count or 0, "Organizations", "🏛️")
with c3:
    render_kpi_card("Total Events", evt_res.count or 0, "All events", "📅")
with c4:
    render_kpi_card("Registrations", reg_total.count or 0, "Event passes issued", "🎫")

render_html("<div style='height: 1.5rem;'></div>")

# Administration Tabs
tab_overview, tab_soc_approvals, tab_evt_approvals = st.tabs([
    "Platform Analytics", 
    "Society Charter Queue", 
    "Event Authorization Queue"
])

# -------------------------------------------------------------
# TAB 1: OVERVIEW & ANALYTICS
# -------------------------------------------------------------
with tab_overview:
    col_chart, col_system = st.columns([3, 1.5])
    
    with col_chart:
        with st.container(border=True):
            render_html("""
            <div style="margin-bottom: 0.75rem;">
                <h3 style="font-size: 1.1rem; font-weight: 700; color: #f1f5f9; margin: 0;">Event Category Distribution</h3>
                <p style="font-size: 0.825rem; color: #64748b; margin-top: 0.25rem;">Campus programming breakdown across areas.</p>
            </div>
            """)
            
            all_events = supabase.table("events").select("category").execute()
            if all_events.data:
                df = pd.DataFrame(all_events.data)
                counts = df['category'].value_counts()
                st.bar_chart(counts, color="#818cf8")
            else:
                render_empty_state("No Events Logged", "Analytics will display once societies begin proposing events.", "📊")
                
    with col_system:
        with st.container(border=True):
            render_html("""
            <div style="margin-bottom: 0.5rem;">
                <h3 style="font-size: 1.1rem; font-weight: 700; color: #f1f5f9; margin: 0;">System Health</h3>
            </div>
            <div style="display: flex; flex-direction: column; gap: 1rem; font-size: 0.875rem; padding-top: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #94a3b8;">Database</span>
                    <span class="badge badge-approved">ONLINE</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #94a3b8;">Auth Engine</span>
                    <span class="badge badge-approved">ACTIVE</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #94a3b8;">AI Matcher</span>
                    <span class="badge badge-ai">GEMINI 3.6</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #94a3b8;">QR Engine</span>
                    <span class="badge badge-approved">SECURE</span>
                </div>
            </div>
            """)
            
            st.divider()
            st.caption(f"Session: {admin_profile.get('email')}")

# -------------------------------------------------------------
# TAB 2: PENDING SOCIETIES
# -------------------------------------------------------------
with tab_soc_approvals:
    render_html("""
    <div style="margin-bottom: 1rem;">
        <h3 style="font-size: 1.15rem; font-weight: 700; color: #f1f5f9; margin: 0;">Society Charter Applications</h3>
        <p style="font-size: 0.825rem; color: #64748b; margin-top: 0.25rem;">Review proposed student organizations seeking official recognition.</p>
    </div>
    """)
    
    pending_soc = supabase.table("societies").select("*, profiles(name, email)").eq("status", "pending").order("created_at").execute()

    if pending_soc.data:
        for soc in pending_soc.data:
            head_info = soc.get('profiles') or {}
            head_name = head_info.get('name', 'Society Head')
            head_email = head_info.get('email', 'No email')
            
            with st.container(border=True):
                colA, colB = st.columns([3.5, 1.2])
                with colA:
                    render_html(f"""
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                        <span class="badge badge-pending">PENDING CHARTER</span>
                        <span style="font-size: 0.8rem; color: #64748b; font-weight: 600;">Dept: {soc.get('department') or 'General'}</span>
                    </div>
                    <h3 style="font-size: 1.25rem; font-weight: 800; color: #f1f5f9; margin: 0 0 0.3rem 0;">{soc['name']}</h3>
                    <p style="font-size: 0.85rem; color: #818cf8; font-weight: 600; margin: 0 0 0.5rem 0;">Requested by {head_name} ({head_email})</p>
                    <p style="font-size: 0.875rem; color: #94a3b8; margin: 0; line-height: 1.5;">{soc.get('description') or 'No description provided.'}</p>
                    """)
                
                with colB:
                    render_html("<div style='height: 1rem;'></div>")
                    if st.button("✅ Approve Charter", key=f"app_soc_{soc['id']}", type="primary", use_container_width=True):
                        supabase.table("societies").update({"status": "active"}).eq("id", soc['id']).execute()
                        st.success(f"Approved charter for {soc['name']}!")
                        st.rerun()
                        
                    if st.button("❌ Reject", key=f"rej_soc_{soc['id']}", use_container_width=True):
                        supabase.table("societies").update({"status": "rejected"}).eq("id", soc['id']).execute()
                        st.warning(f"Rejected charter for {soc['name']}.")
                        st.rerun()
    else:
        render_empty_state("No Pending Societies", "All society charters have been reviewed.", "🏛️")

# -------------------------------------------------------------
# TAB 3: PENDING EVENTS
# -------------------------------------------------------------
with tab_evt_approvals:
    render_html("""
    <div style="margin-bottom: 1rem;">
        <h3 style="font-size: 1.15rem; font-weight: 700; color: #f1f5f9; margin: 0;">Event Authorization Queue</h3>
        <p style="font-size: 0.825rem; color: #64748b; margin-top: 0.25rem;">Review proposed events before publishing to the campus directory.</p>
    </div>
    """)
    
    pending_res = supabase.table("events").select("*, societies(name, department)").eq("status", "pending").order("created_at").execute()

    if pending_res.data:
        for event in pending_res.data:
            soc_data = event.get('societies') or {}
            society_name = soc_data.get('name', 'Unknown Society')
            fee_tag = f"${event.get('fee', 0):.2f}" if event.get("is_paid") else "FREE"
            
            with st.container(border=True):
                colA, colB = st.columns([3.5, 1.2])
                with colA:
                    render_html(f"""
                    <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; flex-wrap: wrap;">
                        <span class="badge badge-pending">PENDING VERIFICATION</span>
                        <span class="badge badge-category">{event.get('category', 'General')}</span>
                        <span style="font-size: 0.8rem; color: #64748b; font-weight: 500;">Ticket: {fee_tag}</span>
                    </div>
                    <h3 style="font-size: 1.25rem; font-weight: 800; color: #f1f5f9; margin: 0 0 0.3rem 0;">{event['title']}</h3>
                    <p style="font-size: 0.85rem; color: #818cf8; font-weight: 600; margin: 0 0 0.6rem 0;">Hosted by {society_name}</p>
                    
                    <div style="display: flex; flex-wrap: wrap; gap: 1.25rem; color: #64748b; font-size: 0.825rem; margin-bottom: 0.75rem;">
                        <span>📅 {event.get('date')} at {event.get('start_time')}</span>
                        <span>📍 {event.get('venue')}</span>
                        <span>👥 Capacity: {event.get('capacity') or 'Unlimited'}</span>
                    </div>
                    <p style="font-size: 0.875rem; color: #94a3b8; margin: 0; line-height: 1.5;">{event.get('description') or 'No description provided.'}</p>
                    """)
                
                with colB:
                    render_html("<div style='height: 1rem;'></div>")
                    if st.button("✅ Authorize Event", key=f"app_evt_{event['id']}", type="primary", use_container_width=True):
                        supabase.table("events").update({"status": "approved"}).eq("id", event['id']).execute()
                        st.success(f"Authorized event: {event['title']}!")
                        st.rerun()
                        
                    if st.button("❌ Reject Event", key=f"rej_evt_{event['id']}", use_container_width=True):
                        supabase.table("events").update({"status": "rejected"}).eq("id", event['id']).execute()
                        st.warning(f"Rejected event proposal: {event['title']}.")
                        st.rerun()
    else:
        render_empty_state("No Pending Events", "The event queue is clear. New proposals will appear here.", "✔️")
