import streamlit as st
import pandas as pd
from utils.db import get_supabase

st.set_page_config(page_title="Admin Dashboard", page_icon="⚙️", layout="wide")

def check_admin():
    st.markdown("""<style>[data-testid="stSidebarNav"] {display: none;}</style>""", unsafe_allow_html=True)
    if st.sidebar.button("Log Out", type="primary"):
        st.session_state.user = None
        st.session_state.role = None
        try: get_supabase().auth.sign_out()
        except: pass
        st.switch_page("app.py")

    if "user" not in st.session_state or st.session_state.user is None:
        st.warning("Please log in from the main page.")
        st.stop()
        
    supabase = get_supabase()
    try:
        res = supabase.table("profiles").select("role").eq("id", st.session_state.user.id).execute()
        if not res.data:
            st.error("No profile found.")
            st.stop()
        db_role = res.data[0].get("role")
        if str(db_role).strip().lower() != "admin":
            st.error("Unauthorized: Admin access required.")
            st.stop()
    except Exception as e:
        st.error(f"Database Fetch Error: {str(e)}")
        st.stop()
        
    return supabase

supabase = check_admin()

st.title("⚙️ Admin Dashboard")
st.write("Manage platform data, approve societies, and review events.")

tab_overview, tab_soc_approvals, tab_evt_approvals = st.tabs(["📊 Platform Overview", "🏢 Pending Societies", "✔️ Pending Events"])

with tab_overview:
    stu_res = supabase.table("profiles").select("id", count="exact").eq("role", "student").execute()
    soc_res = supabase.table("societies").select("id", count="exact").execute()
    evt_res = supabase.table("events").select("id", count="exact").execute()
    reg_total = supabase.table("registrations").select("id", count="exact").execute()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Students", stu_res.count if stu_res.count else 0)
    col2.metric("Total Societies", soc_res.count if soc_res.count else 0)
    col3.metric("Total Events", evt_res.count if evt_res.count else 0)
    col4.metric("Total Registrations", reg_total.count if reg_total.count else 0)
    
    st.divider()
    st.subheader("Event Categories Distribution")
    all_events = supabase.table("events").select("category").execute()
    if all_events.data:
        df = pd.DataFrame(all_events.data)
        counts = df['category'].value_counts()
        st.bar_chart(counts)
    else:
        st.info("No events available for analytics.")

with tab_soc_approvals:
    st.subheader("Pending Society Registrations")
    pending_soc = supabase.table("societies").select("*, profiles(name)").eq("status", "pending").order("created_at").execute()

    if pending_soc.data:
        for soc in pending_soc.data:
            head_name = soc.get('profiles', {}).get('name', 'Unknown Society Head')
            with st.container(border=True):
                colA, colB = st.columns([4, 1])
                with colA:
                    st.markdown(f"### {soc['name']}")
                    st.markdown(f"**Requested by:** {head_name} | **Department:** {soc.get('department', 'N/A')}")
                    st.write(soc.get('description', 'No description provided.'))
                
                with colB:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("✅ Approve", key=f"app_soc_{soc['id']}", use_container_width=True):
                        supabase.table("societies").update({"status": "active"}).eq("id", soc['id']).execute()
                        st.success("Society Approved!")
                        st.rerun()
                    if st.button("❌ Reject", key=f"rej_soc_{soc['id']}", use_container_width=True):
                        supabase.table("societies").update({"status": "rejected"}).eq("id", soc['id']).execute()
                        st.error("Society Rejected.")
                        st.rerun()
    else:
        st.info("No pending societies to review at the moment.")

with tab_evt_approvals:
    st.subheader("Pending Events")
    pending_res = supabase.table("events").select("*, societies(name)").eq("status", "pending").order("created_at").execute()

    if pending_res.data:
        for event in pending_res.data:
            society_name = event.get('societies', {}).get('name', 'Unknown Society')
            with st.container(border=True):
                colA, colB = st.columns([4, 1])
                with colA:
                    st.markdown(f"### {event['title']}")
                    st.markdown(f"**Hosted by:** {society_name} | **Category:** {event['category']} | **Date:** {event['date']}")
                    st.markdown(f"**Venue:** {event['venue']} | **Capacity:** {event['capacity'] or 'Unlimited'} | **Fee:** ${event.get('fee', 0)}")
                    st.write(event.get('description', 'No description provided.'))
                
                with colB:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("✅ Approve Event", key=f"app_evt_{event['id']}", use_container_width=True):
                        supabase.table("events").update({"status": "approved"}).eq("id", event['id']).execute()
                        st.success("Event Approved!")
                        st.rerun()
                    if st.button("❌ Reject", key=f"rej_evt_{event['id']}", use_container_width=True):
                        supabase.table("events").update({"status": "rejected"}).eq("id", event['id']).execute()
                        st.error("Event Rejected.")
                        st.rerun()
    else:
        st.info("No pending events to review at the moment.")
