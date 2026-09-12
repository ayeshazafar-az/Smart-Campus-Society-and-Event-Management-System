import streamlit as st
import pandas as pd
import base64
from utils.db import get_supabase, reset_supabase_session
from utils.ui import (
    apply_custom_theme, 
    render_app_bar, 
    render_page_header, 
    render_kpi_card, 
    render_empty_state,
    render_html
)

st.set_page_config(page_title="Society Operations · CampusPulse", page_icon="🏢", layout="wide")

def check_society_head():
    apply_custom_theme()
    
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("Please sign in from the main portal to access the society dashboard.")
        if st.button("Return to Sign In", type="primary"):
            st.switch_page("app.py")
        st.stop()
        
    supabase = get_supabase()
    res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).execute()
    if not res.data or res.data[0].get("role") != "society_head":
        st.error("Access Restricted: Society Head credentials required.")
        if st.button("Return to Home"):
            st.switch_page("app.py")
        st.stop()
        
    return st.session_state.user.id, res.data[0], supabase

user_id, head_profile, supabase = check_society_head()

# App Bar with integrated logout
if render_app_bar(user_email=st.session_state.user.email, user_role="society_head", user_name=head_profile.get("name")):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.user = None
    st.session_state.role = None
    reset_supabase_session()
    st.switch_page("app.py")

# Fetch Society Associated with Head
soc_res = supabase.table("societies").select("*").eq("head_id", user_id).execute()
society = soc_res.data[0] if soc_res.data else None

if not society:
    render_page_header(
        tag="Society Onboarding",
        title="Charter Your Campus Society",
        description="Establish your official organization profile to propose events and track attendance."
    )
    
    with st.container(border=True):
        render_html("""
        <h3 style="font-size: 1.15rem; font-weight: 700; color: #f1f5f9; margin: 0 0 0.75rem 0;">Submit Society Registration</h3>
        """)
        with st.form("create_society_form"):
            soc_name = st.text_input("Society Name*")
            soc_desc = st.text_area("Description")
            soc_dept = st.text_input("Department (Optional)")
            logo_file = st.file_uploader("Upload Society Logo (Optional)", type=["png", "jpg", "jpeg"], key="soc_logo_uploader")
            
            if st.form_submit_button("Submit for Admin Approval") and soc_name:
                logo_b64 = None
                if logo_file:
                    logo_b64 = f"data:{logo_file.type};base64,{base64.b64encode(logo_file.read()).decode()}"
                    
                # Note the status explicitly set to pending
                supabase.table("societies").insert({
                    "name": soc_name, "description": soc_desc, "department": soc_dept, "head_id": user_id, "status": "pending", "logo": logo_b64
                }).execute()
                st.success("Society profile submitted successfully! It is now pending review.")
                st.rerun()
            else:
                st.error("Please provide a society name.")
else:
    status = society.get('status', 'pending')
    
    # Society Identity Header Card
    badge_type = "approved" if status == "active" else ("pending" if status == "pending" else "rejected")
    dept_label = f"• {society.get('department')}" if society.get('department') else ""
    
    render_html(f"""
    <div class="glass-card" style="margin-bottom: 1.75rem; position: relative;">
        <div style="position: absolute; top: 0; left: 0; right: 0; height: 3px; background: linear-gradient(90deg, #667eea, #764ba2, #22d3ee); background-size: 200% 100%; animation: gradientShift 4s ease infinite; border-radius: 16px 16px 0 0;"></div>
        <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem; padding-top: 0.5rem;">
            <div>
                <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.5rem;">
                    <span class="badge badge-{badge_type}">{status.upper()} CHARTER</span>
                    <span style="font-size: 0.8rem; color: #64748b; font-weight: 600;">{dept_label}</span>
                </div>
                <h1 style="font-size: 1.85rem; font-weight: 800; color: #f1f5f9; margin: 0; letter-spacing: -0.03em;">
                    {society.get('name')}
                </h1>
                <p style="font-size: 0.9rem; color: #94a3b8; margin-top: 0.4rem; max-width: 700px; line-height: 1.5;">
                    {society.get('description') or 'No description provided.'}
                </p>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.7rem; color: #475569; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">Org ID</div>
                <code style="font-size: 0.75rem; color: #818cf8; font-family: 'JetBrains Mono', monospace;">{society['id'][:8]}...</code>
            </div>
        </div>
    </div>
    """)
    
    if status == 'pending':
        st.info("⏳ Your society charter is **under administrative review**. Event publishing unlocks upon verification.")
    elif status == 'rejected':
        st.error("❌ Your society charter was declined. Please contact the student affairs office.")
    else:
        # Fetch Society Aggregate Analytics
        events_res = supabase.table("events").select("*").eq("society_id", society['id']).order("created_at", desc=True).execute()
        all_events = events_res.data or []
        event_ids = [e["id"] for e in all_events]

        regs_by_event = {}
        attended_by_event = {}
        total_society_regs = 0
        total_society_att = 0

        if event_ids:
            all_regs_res = supabase.table("registrations").select("id, event_id").in_("event_id", event_ids).execute()
            all_regs = all_regs_res.data or []
            total_society_regs = len(all_regs)
            all_reg_ids = [r['id'] for r in all_regs]
            
            attended_reg_ids = set()
            if all_reg_ids:
                all_att_res = supabase.table("attendance").select("registration_id").in_("registration_id", all_reg_ids).execute()
                attended_reg_ids = {a['registration_id'] for a in (all_att_res.data or [])}
                total_society_att = len(attended_reg_ids)
            
            for r in all_regs:
                eid = r['event_id']
                regs_by_event[eid] = regs_by_event.get(eid, 0) + 1
                if r['id'] in attended_reg_ids:
                    attended_by_event[eid] = attended_by_event.get(eid, 0) + 1

        turnout_pct = f"{int((total_society_att / total_society_regs) * 100)}%" if total_society_regs > 0 else "N/A"

        # Executive KPI Row
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            render_kpi_card("Total Events", len(all_events), "Hosted & proposed", "📅")
        with k2:
            render_kpi_card("Registrations", total_society_regs, "Confirmed tickets", "👥")
        with k3:
            render_kpi_card("Attendees", total_society_att, "Scanned at door", "✅")
        with k4:
            render_kpi_card("Turnout Rate", turnout_pct, "Attendance rate", "📈")

        render_html("<div style='height: 1.25rem;'></div>")

        # Tabs for Society Operations
        tab_events, tab_create, tab_scan = st.tabs(["Event Portfolio", "Propose New Event", "Venue Check-In Scanner"])

        # -------------------------------------------------------------
        # TAB 1: EVENT PORTFOLIO & STATS
        # -------------------------------------------------------------
        with tab_events:
            render_html("""
            <div style="margin-bottom: 1rem;">
                <h3 style="font-size: 1.15rem; font-weight: 700; color: #f1f5f9; margin: 0;">Managed Campus Events</h3>
            </div>
            """)
            
            if all_events:
                for event in all_events:
                    total_regs = regs_by_event.get(event["id"], 0)
                    attended = attended_by_event.get(event["id"], 0)
                    capacity = event.get('capacity')
                    status_val = event.get('status', 'pending')
                    
                    status_badge_class = "approved" if status_val == "approved" else ("pending" if status_val == "pending" else "rejected")
                    cap_text = f"{total_regs} / {capacity}" if capacity else f"{total_regs} (Unlimited)"
                    event_turnout = f"{int((attended / total_regs) * 100)}%" if total_regs > 0 else "0%"
                    
                    with st.container(border=True):
                        col_e_title, col_e_stats = st.columns([3, 2])
                        with col_e_title:
                            render_html(f"""
                            <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.4rem; flex-wrap: wrap;">
                                <span class="badge badge-{status_badge_class}">{status_val.upper()}</span>
                                <span class="badge badge-category">{event.get('category', 'General')}</span>
                                <span style="font-size: 0.8rem; color: #64748b; font-weight: 500;">📅 {event.get('date')} at {event.get('start_time')}</span>
                            </div>
                            <h3 style="font-size: 1.2rem; font-weight: 700; color: #f1f5f9; margin: 0 0 0.3rem 0;">{event['title']}</h3>
                            <p style="font-size: 0.825rem; color: #64748b; margin: 0 0 0.5rem 0;">📍 {event.get('venue')}</p>
                            <p style="font-size: 0.875rem; color: #94a3b8; margin: 0; line-height: 1.45;">{event.get('description') or 'No description provided.'}</p>
                            """)
                            
                        with col_e_stats:
                            render_html("<div style='height: 0.5rem;'></div>")
                            s1, s2, s3 = st.columns(3)
                            s1.metric("Registered", total_regs)
                            s2.metric("Attended", attended)
                            s3.metric("Turnout", event_turnout)
                            
                            if capacity and capacity > 0:
                                fill_ratio = min(1.0, total_regs / capacity)
                                st.caption(f"Capacity: {int(fill_ratio * 100)}%")
                                st.progress(fill_ratio)
            else:
                render_empty_state("No Events Created Yet", "Use 'Propose New Event' to submit your first event.", "🗓️")

        # -------------------------------------------------------------
        # TAB 2: CREATE EVENT
        # -------------------------------------------------------------
        with tab_create:
            render_html("""
            <div style="margin-bottom: 1rem;">
                <h3 style="font-size: 1.15rem; font-weight: 700; color: #f1f5f9; margin: 0;">Submit New Event Proposal</h3>
                <p style="font-size: 0.825rem; color: #64748b; margin-top: 0.25rem;">Events are forwarded to administration for verification before going public.</p>
            </div>
            """)
            
            with st.container(border=True):
                with st.form("create_event_form"):
                    st.markdown("#### 1. Basic Information")
                    c_title, c_cat = st.columns([2.5, 1.5])
                    with c_title:
                        title = st.text_input("Event Title*", placeholder="e.g. Annual Hackathon & Developer Summit")
                    with c_cat:
                        cats_res = supabase.table("event_categories").select("name").execute()
                        db_cats = [c['name'] for c in cats_res.data] if cats_res.data else []
                        DEFAULT_CATEGORIES = ["General", "Technology", "Science", "Arts", "Sports", "Business", "Academic", "Social", "Workshops"]
                        cat_list = list(dict.fromkeys(db_cats + DEFAULT_CATEGORIES))
                        category = st.selectbox("Event Category*", cat_list)
                        
                    desc = st.text_area("Event Description*", placeholder="Provide agenda, speakers, prerequisites...")
                    
                    st.divider()
                    st.markdown("#### 2. Schedule & Venue")
                    col1, col2 = st.columns(2)
                    with col1:
                        date = col1.date_input("Event Date*")
                        time_start = col1.time_input("Start Time*")
                    with col2:
                        venue = col2.text_input("Venue / Hall*", placeholder="e.g. Auditorium Hall B")
                        time_end = col2.time_input("End Time (Optional)")
                        
                    st.divider()
                    st.markdown("#### 3. Capacity & Pricing")
                    col3, col4 = st.columns(2)
                    with col3:
                        capacity = col3.number_input("Capacity (0 for unlimited)", min_value=0, value=100)
                    with col4:
                        is_paid = col4.checkbox("Is a Paid Event?")
                        fee = col4.number_input("Fee Amount (if paid)", min_value=0.0, value=0.0)
                    
                    poster_file = st.file_uploader("Upload Event Poster (Optional)", type=["png", "jpg", "jpeg"], key="evt_poster_uploader")
                    
                    render_html("<div style='height: 12px;'></div>")
                    if st.form_submit_button("Submit Event for Review", type="primary", use_container_width=True):
                        if title.strip() and date and venue.strip() and desc.strip():
                            poster_b64 = None
                            if poster_file:
                                poster_b64 = f"data:{poster_file.type};base64,{base64.b64encode(poster_file.read()).decode()}"
                                
                            supabase.table("events").insert({
                                "society_id": society['id'],
                                "title": title.strip(),
                                "description": desc.strip(),
                                "category": category,
                                "date": str(date),
                                "start_time": str(time_start),
                                "end_time": str(time_end) if time_end else None,
                                "venue": venue.strip(),
                                "capacity": capacity if capacity > 0 else None,
                                "is_paid": is_paid,
                                "fee": float(fee) if is_paid else 0.0,
                                "status": "pending",
                                "poster": poster_b64
                            }).execute()
                            st.success("🎉 Event proposal submitted! Awaiting administration approval.")
                            st.rerun()
                        else:
                            st.error("Please fill in all required fields.")

        # -------------------------------------------------------------
        # TAB 3: SCAN QR ATTENDANCE
        # -------------------------------------------------------------
        with tab_scan:
            render_html("""
            <div style="margin-bottom: 1rem;">
                <h3 style="font-size: 1.15rem; font-weight: 700; color: #f1f5f9; margin: 0;">Venue Check-In Console</h3>
                <p style="font-size: 0.825rem; color: #64748b; margin-top: 0.25rem;">Verify student passes at the door by entering the QR token code.</p>
            </div>
            """)
            
            col_scan_box, col_scan_side = st.columns([2.5, 1.5])
            
            with col_scan_box:
                with st.container(border=True):
                    render_html("""
                    <h4 style="font-size: 1rem; font-weight: 700; color: #f1f5f9; margin: 0 0 0.75rem 0;">Scan or Enter Pass Token</h4>
                    """)
                    token_input = st.text_input(
                        "QR Pass Token", 
                        placeholder="Paste or scan token (e.g. 5d5a2b1f-7f12-4c28-98e3-...)",
                        key="qr_token_scanner_input"
                    )
                    
                    render_html("<div style='height: 8px;'></div>")
                    if st.button("Validate & Mark Attendance", type="primary", use_container_width=True):
                        if token_input.strip():
                            reg = supabase.table("registrations").select("*, events(*), profiles(name, email)").eq("qr_token", token_input.strip()).execute()
                            if not reg.data:
                                st.error("❌ Invalid Token: Registration pass not found.")
                            else:
                                r_data = reg.data[0]
                                event_info = r_data.get("events")
                                attendee_name = r_data.get("profiles", {}).get("name", "Student")
                                
                                if not event_info or event_info.get("society_id") != society["id"]:
                                    st.error("❌ Access Denied: This pass is for a different society's event.")
                                else:
                                    att_check = supabase.table("attendance").select("id").eq("registration_id", r_data["id"]).execute()
                                    if att_check.data:
                                        st.warning(f"⚠️ Duplicate Scan: **{attendee_name}** already checked in for **{event_info.get('title')}**.")
                                    else:
                                        supabase.table("attendance").insert({"registration_id": r_data["id"]}).execute()
                                        st.success(f"✅ Attendance Recorded: **{attendee_name}** admitted to **{event_info.get('title')}**.")
                        else:
                            st.error("Please input a valid pass token.")
                            
            with col_scan_side:
                with st.container(border=True):
                    render_html("""
                    <h4 style="font-size: 1rem; font-weight: 700; color: #f1f5f9; margin: 0 0 0.75rem 0;">Check-In Guidelines</h4>
                    """)
                    st.markdown("""
                    - **Single Admission**: Each token is valid for one entry.
                    - **Instant Validation**: Duplicates are immediately detected.
                    - **Society Scoped**: Passes for other societies can't be scanned here.
                    - **Real-Time Sync**: Turnout stats update across the portal.
                    """)
