# 🎓 Smart Campus Society & Event Management System

**Hackathon MVP Version 1.0**

A centralized digital platform where university societies can manage events and students can discover, register for, and attend verified campus events from one single place. Built to solve the fragmentation of university communications into separate platforms and WhatsApp groups.

## ✨ Core Features
- **🏢 Role-based Dashboards:** Dedicated tailored workflows for Students, Society Heads, and Admins.
- **✅ Event Verification Pipeline:** Admins securely approve or reject events proposed by societies before they go public.
- **🎫 Dynamic Registration:** Automatically enforces live capacity limits and instantly generates secure, unique QR code tokens for registrants.
- **📷 QR Attendance System:** Scan unique student QR tokens at the venue entrance for instant, duplicate-proof attendance logging.
- **🤖 AI Event Recommendations:** Leverages the powerful Google Gemini 1.5 Flash API to analyze a student's past registrations and profile interests, suggesting upcoming events they're most likely to enjoy.

## 🛠 Tech Stack
- **Frontend & App Engine:** Python 3 & Streamlit
- **Backend (Database & Auth):** Supabase (PostgreSQL)
- **AI Integration:** Google Gemini API
- **Utilities:** `qrcode`, `python-dotenv`, `pandas`

## 🚀 Local Installation

**1. Clone the repository:**
```bash
git clone https://github.com/ayeshazafar-az/Smart-Campus-Society-and-Event-Management-System.git
cd Smart-Campus-Society-and-Event-Management-System
```

**2. Install dependencies:**
Make sure you have Python installed, then run:
```bash
pip install -r requirements.txt
```

**3. Environment Setup:**
Create a `.env` file in the root directory (you can use `.env.example` as a template) and configure your keys:
```env
SUPABASE_URL="your_supabase_project_url"
SUPABASE_KEY="your_supabase_anon_key"
GEMINI_API_KEY="your_gemini_api_key"
```

**4. Database Configuration:**
Copy and run the SQL commands provided in `supabase_schema.sql` inside your Supabase project's SQL Editor. This will automatically generate all necessary tables (Profiles, Societies, Events, Registrations, Attendance, Categories) and authentication triggers.

**5. Run the Application:**
```bash
python -m streamlit run app.py
```

## 💡 How to Test the Demo
1. Register an account and set your role to **Society Head**. Create your society profile and submit a new test event.
2. Register a new account as an **Admin** (or adjust your role in the DB). Approve the pending event from the Admin Dashboard.
3. Register a third account as a **Student**. Browse the upcoming event feed, generate AI recommendations, and register. 
4. Check your student *My Registrations* tab for your freshly minted QR code token.
5. Log back into the **Society Head** account, navigate to the *Scan QR Attendance* tab, and enter the student's token. Attendance is automatically marked and analytics are updated in real-time!
