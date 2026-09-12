import os
import google.generativeai as genai
from utils.db import get_supabase

def get_recommendations(user_id: str) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API key is not configured in the environment variables."
        
    genai.configure(api_key=api_key)
    supabase = get_supabase()
    
    try:
        # Fetch Student Profile
        prof_res = supabase.table("profiles").select("*").eq("id", user_id).execute()
        if not prof_res.data:
            return "Could not load student profile."
        profile = prof_res.data[0]
        
        # Fetch Past Registrations
        regs_res = supabase.table("registrations").select("events(title, category)").eq("student_id", user_id).execute()
        past_events = []
        if regs_res.data:
            for r in regs_res.data:
                e = r.get("events")
                if e:
                    past_events.append(f"{e['title']} ({e['category']})")
        
        # Fetch Upcoming Available Events
        avail_res = supabase.table("events").select("title, category, description, date, venue").eq("status", "approved").execute()
        if not avail_res.data:
            return "There are no upcoming events available to recommend at this time."
            
        prompt = f"""
        You are an AI assistant for a smart campus event platform.
        Student Name: {profile.get('name', 'Student')}
        Department: {profile.get('department', 'Not specified')}
        Interests: {profile.get('interests', 'Not specified')}
        
        Past Events Attended/Registered:
        {', '.join(past_events) if past_events else 'None yet.'}
        
        Upcoming Approved Events on Campus:
        """
        for count, e in enumerate(avail_res.data, 1):
            prompt += f"{count}. {e['title']} ({e['category']}) on {e['date']} @ {e['venue']}. Details: {e['description'][:100]}\n"
            
        prompt += """
        Based strictly on the student's background and past events attended, pick 2-3 most relevant events from the 'Upcoming Approved Events' list. 
        Format the response in engaging markdown. Be enthusiastic, clear, and brief. Start directly with the recommendations.
        """
        
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"Warning: AI Recommendation encountered an error: {str(e)}"
