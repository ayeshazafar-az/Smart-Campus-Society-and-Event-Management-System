import streamlit as st
import uuid
import datetime
from utils.db import get_supabase, reset_supabase_session
from utils.qr_ops import get_qr_base64
from utils.ai_recs import get_recommendations
from utils.ui import (
    apply_custom_theme, 
    render_app_bar, 
    render_page_header, 
    render_kpi_card, 
    render_empty_state,
    render_html
)

st.set_page_config(page_title="Student Portal · CampusPulse", page_icon="🎓", layout="wide")

def check_student():
    apply_custom_theme()
    
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("Please sign in from the main portal to access the student dashboard.")
        if st.button("Return to Sign In", type="primary"):
            st.switch_page("app.py")
        st.stop()
        
    supabase = get_supabase()
    res = supabase.table("profiles").select("*").eq("id", st.session_state.user.id).execute()
    if not res.data or res.data[0].get("role") != "student":
        st.error("Access Restricted: Student credentials required.")
        if st.button("Return to Home"):
            st.switch_page("app.py")
        st.stop()
        
    return st.session_state.user.id, res.data[0], supabase

user_id, student_profile, supabase = check_student()

# App Bar with integrated logout
if render_app_bar(user_email=st.session_state.user.email, user_role="student", user_name=student_profile.get("name")):
    try:
        supabase.auth.sign_out()
    except Exception:
        pass
    st.session_state.user = None
    st.session_state.role = None
    reset_supabase_session()
    st.switch_page("app.py")

# Student Greeting & Page Header
student_name = student_profile.get("name") or "Student"
render_page_header(
    tag="Student Hub",
    title=f"Welcome back, {student_name}",
    description="Discover campus events, manage your digital QR passes, and explore AI recommendations."
)

# Fetch Student Metrics
regs_call = supabase.table("registrations").select("id, event_id").eq("student_id", user_id).execute()
registered_event_ids = [r["event_id"] for r in (regs_call.data or [])]
registered_ids = [r["id"] for r in (regs_call.data or [])]

attended_count = 0
if registered_ids:
    att_call = supabase.table("attendance").select("id").in_("registration_id", registered_ids).execute()
    attended_count = len(att_call.data) if att_call.data else 0

total_events_call = supabase.table("events").select("id", count="exact").eq("status", "approved").execute()
approved_events_count = total_events_call.count or 0

# KPI Stat Cards Row
c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card("Campus Events", approved_events_count, "Live verified events", "🏛️")
with c2:
    render_kpi_card("My Registrations", len(registered_event_ids), "Active event passes", "🎫")
with c3:
    render_kpi_card("Events Attended", attended_count, "Verified check-ins", "✅")
with c4:
    dept = student_profile.get("department") or "General"
    render_kpi_card("Major / Track", dept, "Academic department", "🎓")

render_html("<div style='height: 1.5rem;'></div>")

# Main Navigation Tabs
tab_discover, tab_passes, tab_ai, tab_profile = st.tabs(["Discover Events", "My Digital Passes", "AI Recommendations", "⚙️ Profile Settings"])

# -------------------------------------------------------------
# TAB 1: DISCOVER EVENTS
# -------------------------------------------------------------
with tab_discover:
    render_html("""
    <div style="margin-bottom: 1rem;">
        <h3 style="font-size: 1.15rem; font-weight: 700; color: #f1f5f9; margin: 0;">Explore Upcoming Events</h3>
    </div>
    """)
    
    # Filter & Search Controls
    filter_col1, filter_col2, filter_col3 = st.columns([3, 1.5, 1.5])
    with filter_col1:
        search_q = st.text_input("Search events", placeholder="Search by title, topic, or keyword...", label_visibility="collapsed")
    with filter_col2:
        category_filter = st.selectbox(
            "Category", 
            ["All Categories", "Technology", "Science", "Arts", "Sports", "Business", "General"],
            label_visibility="collapsed"
        )
    with filter_col3:
        pricing_filter = st.selectbox(
            "Pricing",
            ["All Events", "Free Only", "Paid Only"],
            label_visibility="collapsed"
        )

    # Fetch Approved Events (Excluding Expired)
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    events_res = supabase.table("events").select("*, societies(name)").eq("status", "approved").gte("date", today_str).order("date").execute()

    if events_res.data:
        event_ids = [e["id"] for e in events_res.data]
        reg_counts = {}
        if event_ids:
            all_regs = supabase.table("registrations").select("event_id").in_("event_id", event_ids).execute()
            for r in (all_regs.data or []):
                eid = r["event_id"]
                reg_counts[eid] = reg_counts.get(eid, 0) + 1

        # Apply Filters
        filtered_events = []
        for e in events_res.data:
            if search_q.strip():
                q = search_q.lower()
                if q not in e["title"].lower() and q not in e.get("category", "").lower() and q not in e.get("description", "").lower():
                    continue
            if category_filter != "All Categories" and e.get("category", "").lower() != category_filter.lower():
                continue
            if pricing_filter == "Free Only" and e.get("is_paid"):
                continue
            if pricing_filter == "Paid Only" and not e.get("is_paid"):
                continue
            filtered_events.append(e)

        if filtered_events:
            for event in filtered_events:
                society_name = event.get('societies', {}).get('name', 'Campus Society')
                current_regs = reg_counts.get(event["id"], 0)
                capacity = event.get('capacity')
                is_sold_out = bool(capacity and current_regs >= capacity)
                is_registered = event["id"] in registered_event_ids
                
                spots_text = f"{capacity - current_regs} of {capacity} spots left" if capacity else "Unlimited Capacity"
                fill_pct = min(100, int((current_regs / capacity) * 100)) if capacity and capacity > 0 else 0
                fee_badge = f'<span class="badge badge-paid">${event.get("fee", 0):.2f}</span>' if event.get("is_paid") else '<span class="badge badge-free">FREE</span>'
                category_badge = f'<span class="badge badge-category">{event.get("category", "General")}</span>'
                poster_html = f'<img src="{event.get("poster")}" style="width: 100%; object-fit: cover; border-radius: 12px; margin-bottom: 1rem; max-height: 250px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);" />' if event.get("poster") else ''

                with st.container(border=True):
                    col_info, col_action = st.columns([3.2, 1])
                    
                    with col_info:
                        render_html(f"""
                        {poster_html}
                        <div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem;">
                            {category_badge}
                            {fee_badge}
                        </div>
                        <h3 style="font-size: 1.25rem; font-weight: 700; color: #f1f5f9; margin: 0 0 0.3rem 0;">{event['title']}</h3>
                        <p style="font-size: 0.85rem; color: #818cf8; font-weight: 600; margin: 0 0 0.5rem 0;">Hosted by {society_name}</p>
                        <p style="font-size: 0.875rem; color: #94a3b8; margin: 0 0 0.75rem 0; line-height: 1.5;">{event.get('description') or 'No description provided.'}</p>
                        
                        <div style="display: flex; flex-wrap: wrap; gap: 1.25rem; color: #64748b; font-size: 0.825rem; font-weight: 500;">
                            <span>📅 {event.get('date', 'TBA')}</span>
                            <span>⏰ {event.get('start_time', 'TBA')}</span>
                            <span>📍 {event.get('venue', 'Venue TBA')}</span>
                            <span>👥 {spots_text}</span>
                        </div>
                        """)
                        
                        if capacity:
                            st.progress(fill_pct / 100)

                    with col_action:
                        render_html("<div style='height: 1.5rem;'></div>")
                        if is_registered:
                            st.button("✅ Registered", key=f"btn_reg_{event['id']}", disabled=True, use_container_width=True)
                        elif is_sold_out:
                            st.button("❌ Sold Out", key=f"btn_sold_{event['id']}", disabled=True, use_container_width=True)
                        else:
                            with st.popover("Register Now", use_container_width=True):
                                st.markdown(f"**Confirm Pass for {event['title']}**")
                                st.caption(f"Host: {society_name} | Venue: {event.get('venue')}")
                                
                                if event.get("is_paid"):
                                    st.info(f"💳 Registration Fee: **${event.get('fee', 0):.2f}** (Sandbox)")
                                    st.text_input("Cardholder Name", value=student_name, key=f"card_name_{event['id']}")
                                    st.text_input("Card Number", value="•••• •••• •••• 4242", type="password", key=f"card_num_{event['id']}")
                                    
                                if st.button("Confirm Registration", key=f"confirm_{event['id']}", type="primary", use_container_width=True):
                                    # Atomic capacity & duplicate re-check
                                    cap_check = supabase.table("registrations").select("id", count="exact").eq("event_id", event["id"]).execute()
                                    latest_count = cap_check.count or 0
                                    cap_limit = event.get("capacity")
                                    
                                    dup_check = supabase.table("registrations").select("id").eq("event_id", event["id"]).eq("student_id", user_id).execute()
                                    if dup_check.data:
                                        st.warning("You are already registered for this event!")
                                    elif cap_limit and latest_count >= cap_limit:
                                        st.error("Registration closed: Event reached full capacity.")
                                    else:
                                        qr_token = str(uuid.uuid4())
                                        supabase.table("registrations").insert({
                                            "event_id": event["id"],
                                            "student_id": user_id,
                                            "payment_status": "paid" if event.get("is_paid") else "unpaid",
                                            "registration_status": "confirmed",
                                            "qr_token": qr_token
                                        }).execute()
                                        st.success("🎉 Registration Confirmed! Your pass is ready in 'My Passes'.")
                                        st.rerun()
        else:
            render_empty_state("No Events Match Your Filters", "Try adjusting your search keywords or filters.", "🔍")
    else:
        render_empty_state("No Approved Events Found", "Events will appear here once approved by administration.", "📅")

# -------------------------------------------------------------
# TAB 2: MY DIGITAL EVENT PASSES
# -------------------------------------------------------------
with tab_passes:
    render_html("""
    <div style="margin-bottom: 1rem;">
        <h3 style="font-size: 1.15rem; font-weight: 700; color: #f1f5f9; margin: 0;">Your Verified Digital Passes</h3>
        <p style="font-size: 0.825rem; color: #64748b; margin-top: 0.25rem;">Present the QR code at the event entrance for instant verification.</p>
    </div>
    """)
    
    my_regs = supabase.table("registrations").select("*, events(*, societies(name))").eq("student_id", user_id).order("registered_at", desc=True).execute()
    
    if my_regs.data:
        for r in my_regs.data:
            e = r.get("events")
            if not e:
                continue
                
            soc_name = e.get('societies', {}).get('name', 'Campus Society')
            qr_b64 = get_qr_base64(r["qr_token"])
            ticket_id_short = r["qr_token"][:8].upper()
            
            pay_badge = '<span class="badge badge-paid">PAID</span>' if r.get("payment_status") == "paid" else '<span class="badge badge-free">FREE PASS</span>'
            status_badge = '<span class="badge badge-confirmed">CONFIRMED</span>'
            
            render_html(f"""
            <div class="ticket-pass">
                <div class="ticket-main">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.6rem;">
                        <div style="display: flex; gap: 0.4rem; flex-wrap: wrap;">
                            <span class="badge badge-category">{e.get('category', 'Event')}</span>
                            {pay_badge}
                            {status_badge}
                        </div>
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #475569; font-weight: 600;">PASS #{ticket_id_short}</span>
                    </div>
                    
                    <h2 style="font-size: 1.35rem; font-weight: 800; color: #f1f5f9; margin: 0 0 0.3rem 0;">{e.get('title')}</h2>
                    <p style="font-size: 0.875rem; color: #818cf8; font-weight: 600; margin: 0 0 1rem 0;">Organized by {soc_name}</p>
                    
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 0.85rem; padding-top: 0.85rem; border-top: 1px solid rgba(255,255,255,0.06);">
                        <div>
                            <div style="font-size: 0.65rem; color: #475569; text-transform: uppercase; font-weight: 700; letter-spacing: 0.06em;">Date</div>
                            <div style="font-size: 0.875rem; font-weight: 600; color: #e2e8f0;">{e.get('date', 'TBA')}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.65rem; color: #475569; text-transform: uppercase; font-weight: 700; letter-spacing: 0.06em;">Time</div>
                            <div style="font-size: 0.875rem; font-weight: 600; color: #e2e8f0;">{e.get('start_time', 'TBA')}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.65rem; color: #475569; text-transform: uppercase; font-weight: 700; letter-spacing: 0.06em;">Venue</div>
                            <div style="font-size: 0.875rem; font-weight: 600; color: #e2e8f0;">{e.get('venue', 'TBA')}</div>
                        </div>
                        <div>
                            <div style="font-size: 0.65rem; color: #475569; text-transform: uppercase; font-weight: 700; letter-spacing: 0.06em;">Attendee</div>
                            <div style="font-size: 0.875rem; font-weight: 600; color: #e2e8f0;">{student_name}</div>
                        </div>
                    </div>
                </div>
                <div class="ticket-qr">
                    <img src="{qr_b64}" width="130" style="border-radius: 10px; box-shadow: 0 4px 16px rgba(0,0,0,0.3); border: 2px solid rgba(255,255,255,0.06);" />
                    <div style="font-size: 0.7rem; color: #64748b; font-weight: 700; margin-top: 0.6rem; text-transform: uppercase; letter-spacing: 0.08em;">Scan at Entrance</div>
                    <code style="font-size: 0.6rem; color: #475569; margin-top: 0.2rem; font-family: 'JetBrains Mono', monospace;">{r['qr_token'][:13]}...</code>
                </div>
            </div>
            """)
    else:
        render_empty_state(
            "No Event Passes Yet",
            "Browse events in 'Discover' and reserve your first pass.",
            "🎫"
        )

# -------------------------------------------------------------
# TAB 3: GEMINI AI RECOMMENDATIONS
# -------------------------------------------------------------
with tab_ai:
    render_html("""
    <div style="margin-bottom: 1rem;">
        <h3 style="font-size: 1.15rem; font-weight: 700; color: #f1f5f9; margin: 0;">Gemini AI Campus Intelligence</h3>
        <p style="font-size: 0.825rem; color: #64748b; margin-top: 0.25rem;">Personalized event suggestions based on your profile and history.</p>
    </div>
    """)

    ai_col1, ai_col2 = st.columns([3, 1])
    with ai_col1:
        render_html(f"""
        <div class="glass-card" style="margin-bottom: 1rem;">
            <div style="display: flex; align-items: center; gap: 0.85rem;">
                <div style="width: 40px; height: 40px; border-radius: 10px; background: rgba(167, 139, 250, 0.12); border: 1px solid rgba(167, 139, 250, 0.2); color: #a78bfa; display: flex; align-items: center; justify-content: center; font-size: 1.2rem;">✨</div>
                <div>
                    <h4 style="font-size: 0.95rem; font-weight: 700; color: #f1f5f9; margin: 0;">Contextual Matching Engine</h4>
                    <p style="font-size: 0.825rem; color: #64748b; margin: 0;">Tailored to your major (<strong style="color: #818cf8;">{dept}</strong>) and {len(registered_event_ids)} past registrations.</p>
                </div>
            </div>
        </div>
        """)
    with ai_col2:
        btn_gen = st.button("Generate Recommendations", type="primary", use_container_width=True)

    if btn_gen:
        with st.spinner("Analyzing profile & catalog with Gemini AI..."):
            recs_text = get_recommendations(user_id)
            st.session_state["cached_student_recs"] = recs_text

    if "cached_student_recs" in st.session_state:
        render_html(f"""
        <div class="ai-container">
            <span class="badge badge-ai" style="margin-bottom: 0.75rem; display: inline-flex;">✨ Gemini AI · Personalized Match</span>
            <div style="font-size: 0.925rem; line-height: 1.7; color: #e2e8f0;">
                {st.session_state['cached_student_recs']}
            </div>
        </div>
        """)
    elif not btn_gen:
        render_empty_state(
            "Ready for Insights",
            "Click 'Generate Recommendations' to get AI-powered event suggestions.",
            "🤖"
        )

# -------------------------------------------------------------
# TAB 4: PROFILE SETTINGS
# -------------------------------------------------------------
with tab_profile:
    render_html("""
    <div style="margin-bottom: 1rem;">
        <h3 style="font-size: 1.15rem; font-weight: 700; color: #f1f5f9; margin: 0;">Profile Configuration</h3>
        <p style="font-size: 0.825rem; color: #64748b; margin-top: 0.25rem;">Fine-tune your major and interests for razor-sharp Gemini AI recommendations.</p>
    </div>
    """)
    with st.container(border=True):
        with st.form("update_profile_form"):
            current_dept = student_profile.get("department") or ""
            current_interests = student_profile.get("interests") or ""
            new_dept = st.text_input("Academic Department / Major", value=current_dept, placeholder="e.g., Computer Science")
            new_interests = st.text_area("Event Interests", value=current_interests, placeholder="e.g., AI, Robotics, Music, Tech Seminars")
            
            if st.form_submit_button("Save Preferences", type="primary", use_container_width=True):
                supabase.table("profiles").update({"department": new_dept, "interests": new_interests}).eq("id", user_id).execute()
                st.success("Preferences securely saved! Your AI recommendations will now adapt.")
                st.rerun()
