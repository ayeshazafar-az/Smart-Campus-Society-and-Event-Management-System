import streamlit as st
import pandas as pd
from utils.db import get_supabase

st.set_page_config(page_title="Society Dashboard", page_icon="🏢", layout="wide")

def check_society_head():
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("Please log in from the main page.")
        st.stop()
        
    supabase = get_supabase()
    res = supabase.table("profiles").select("role").eq("id", st.session_state.user.id).execute()
    if not res.data or res.data[0].get("role") != "society_head":
        st.error("Unauthorized: Society Head access required.")
        st.stop()
    return st.session_state.user.id, supabase

user_id, supabase = check_society_head()

st.title("🏢 Society Dashboard")
st.write("Manage your society profile, create events, and track attendance!")

soc_res = supabase.table("societies").select("*").eq("head_id", user_id).execute()
society = soc_res.data[0] if soc_res.data else None

if not society:
    st.info("You haven't set up your society profile yet. Please complete it first.")
    with st.form("create_society_form"):
        soc_name = st.text_input("Society Name*")
        soc_desc = st.text_area("Description")
        soc_dept = st.text_input("Department (Optional)")
        if st.form_submit_button("Create Society") and soc_name:
            supabase.table("societies").insert({
                "name": soc_name, "description": soc_desc, "department": soc_dept, "head_id": user_id
            }).execute()
            st.success("Society created successfully!")
            st.rerun()
else:
    st.subheader(f"✨ {society.get('name')}")
    st.write(society.get("description", ""))
    
    st.divider()
    tab_events, tab_create, tab_scan = st.tabs(["📊 My Events & Stats", "➕ Create New Event", "📷 Scan QR Attendance"])
    
    with tab_events:
        events_res = supabase.table("events").select("*").eq("society_id", society['id']).order("created_at", desc=True).execute()
        if events_res.data:
            for event in events_res.data:
                # Analytics computation per event
                regs_res = supabase.table("registrations").select("id").eq("event_id", event["id"]).execute()
                total_regs = len(regs_res.data) if regs_res.data else 0
                
                # We can't do direct deep joined count easily in simple MVP, so we iterate or use simple map
                # But since we have event_id -> registrations -> attendance, let's get attendance list
                # Or fetch all attendance for these regs
                reg_ids = [r['id'] for r in (regs_res.data or [])]
                attended = 0
                if reg_ids:
                    att_res = supabase.table("attendance").select("id").in_("registration_id", reg_ids).execute()
                    attended = len(att_res.data) if att_res.data else 0
                
                with st.expander(f"[{event['status'].upper()}] {event['title']} - {event['date']}"):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Registrations", total_regs)
                    c2.metric("Attended", attended)
                    c3.metric("Capacity", event.get('capacity') or "Unlimited")
                    
                    st.write(f"**Venue:** {event['venue']} | **Time:** {event['start_time']}")
                    st.write(f"**Description:** {event['description']}")
        else:
            st.info("You have not created any events yet.")
            
    with tab_create:
        with st.form("create_event_form"):
            st.write("Submit a new event for Admin approval:")
            title = st.text_input("Event Title*")
            desc = st.text_area("Description")
            
            cats_res = supabase.table("event_categories").select("name").execute()
            cat_list = [c['name'] for c in cats_res.data] if cats_res.data else ["General"]
            category = st.selectbox("Category", cat_list)
            
            col1, col2 = st.columns(2)
            date = col1.date_input("Event Date*")
            time_start = col1.time_input("Start Time*")
            time_end = col2.time_input("End Time")
            venue = col2.text_input("Venue*")
            
            col3, col4 = st.columns(2)
            capacity = col3.number_input("Capacity (0 for unlimited)", min_value=0, value=100)
            is_paid = col4.checkbox("Is a Paid Event?")
            fee = col4.number_input("Fee Amount (if paid)", min_value=0.0, value=0.0)
            
            if st.form_submit_button("Submit Event"):
                if title and date and venue:
                    supabase.table("events").insert({
                        "society_id": society['id'], "title": title, "description": desc, "category": category,
                        "date": str(date), "start_time": str(time_start), "end_time": str(time_end) if time_end else None,
                        "venue": venue, "capacity": capacity if capacity > 0 else None, "is_paid": is_paid,
                        "fee": fee if is_paid else 0.0, "status": "pending"
                    }).execute()
                    st.success("Event submitted successfully! It is now pending Admin approval.")
                else:
                    st.error("Please fill all required (*) fields.")

    with tab_scan:
        st.write("Scan a student's QR code (or manually input the unique token) at the event entrance.")
        token_input = st.text_input("QR Token", placeholder="e.g. 5d5a2b1f-...")
        
        if st.button("Validate & Mark Attendance", type="primary"):
            if token_input:
                # 1. Find registration
                reg = supabase.table("registrations").select("*, events(society_id)").eq("qr_token", token_input).execute()
                if not reg.data:
                    st.error("❌ Invalid QR Token. Registration not found.")
                else:
                    r_data = reg.data[0]
                    # 2. Check if event belongs to this society
                    if r_data["events"]["society_id"] != society["id"]:
                        st.error("❌ This QR token is for an event hosted by a different society.")
                    else:
                        # 3. Check duplicate attendance
                        att_check = supabase.table("attendance").select("id").eq("registration_id", r_data["id"]).execute()
                        if att_check.data:
                            st.warning("⚠️ Duplicate Scan! This student has already been marked as attended.")
                        else:
                            # 4. Mark attended
                            supabase.table("attendance").insert({"registration_id": r_data["id"]}).execute()
                            st.success("✅ Attendance successfully recorded!")
            else:
                st.error("Please enter a token.")
