import streamlit as st
import uuid
from utils.db import get_supabase
from utils.qr_ops import get_qr_base64
from utils.ai_recs import get_recommendations

st.set_page_config(page_title="Student Dashboard", page_icon="🎓", layout="wide")

def check_student():
    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("Please log in from the main page.")
        st.stop()
    supabase = get_supabase()
    return st.session_state.user.id, supabase

user_id, supabase = check_student()

st.title("🎓 Student Dashboard")
st.write("Discover events, manage registrations, and view your AI recommendations.")

# Check current registrations to lock buttons
regs_call = supabase.table("registrations").select("event_id").eq("student_id", user_id).execute()
registered_event_ids = [r["event_id"] for r in regs_call.data] if regs_call.data else []

tab1, tab2, tab3 = st.tabs(["Upcoming Events", "My Registrations", "AI Recommendations ✨"])

with tab1:
    st.subheader("Discover Campus Events")
    
    search_q = st.text_input("Search events...", "")
    events_res = supabase.table("events").select("*, societies(name)").eq("status", "approved").order("date").execute()
    
    if events_res.data:
        for event in events_res.data:
            if search_q.lower() not in event['title'].lower() and search_q.lower() not in event['category'].lower():
                continue
                
            society_name = event.get('societies', {}).get('name', 'Unknown Society')
            
            # Capacity check
            cap_res = supabase.table("registrations").select("id", count="exact").eq("event_id", event["id"]).execute()
            current_regs = cap_res.count if cap_res.count else 0
            capacity = event.get('capacity')
            spots_left = (capacity - current_regs) if capacity else "Unlimited"
            
            with st.container(border=True):
                colA, colB = st.columns([3, 1])
                with colA:
                    st.markdown(f"### {event['title']}")
                    st.markdown(f"**By:** {society_name} | **Category:** {event['category']}")
                    st.markdown(f"📅 {event['date']} at {event['start_time']} | 📍 {event['venue']}")
                    st.markdown(f"**Fee:** {f'${event.fee}' if event.get('is_paid') else 'Free'} | **Spots left:** {spots_left}")
                    st.write(event.get('description', ''))
                
                with colB:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if event["id"] in registered_event_ids:
                        st.success("✅ Registered")
                    elif capacity and current_regs >= capacity:
                        st.error("Sold Out")
                    else:
                        with st.popover("Register Now"):
                            st.write(f"Confirm Registration for **{event['title']}**")
                            # Simulated payment if paid
                            if event.get("is_paid"):
                                st.info("💳 Payment Required (Simulated)")
                                st.text_input("Card Number", "4242 4242 4242 4242", type="password")
                            
                            if st.button("Confirm", key=f"confirm_{event['id']}"):
                                qr_token = str(uuid.uuid4())
                                supabase.table("registrations").insert({
                                    "event_id": event["id"],
                                    "student_id": user_id,
                                    "payment_status": "paid" if event.get("is_paid") else "unpaid",
                                    "registration_status": "confirmed",
                                    "qr_token": qr_token
                                }).execute()
                                st.success("Registration Successful!")
                                st.rerun()
    else:
        st.info("No upcoming approved events available.")

with tab2:
    st.subheader("My Registrations & QR Codes")
    my_regs = supabase.table("registrations").select("*, events(*)").eq("student_id", user_id).execute()
    
    if my_regs.data:
        for r in my_regs.data:
            e = r["events"]
            if not e: continue
            
            with st.container(border=True):
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.markdown(f"**{e['title']}**")
                    st.write(f"📅 {e['date']} | 📍 {e['venue']}")
                    st.write(f"QR Token: `{r['qr_token'][:8]}...`")
                    st.caption("Show this QR at the venue entrance.")
                    
                with c2:
                    qr_b64 = get_qr_base64(r["qr_token"])
                    st.markdown(f'<img src="{qr_b64}" width="150">', unsafe_allow_html=True)
    else:
        st.info("You haven't registered for any events yet.")

with tab3:
    st.subheader("✨ AI Recommended Events for You")
    if st.button("Generate Recommendations", type="primary"):
        with st.spinner("Analyzing your profile and scanning campus events..."):
            recs = get_recommendations(user_id)
            st.markdown(recs)
