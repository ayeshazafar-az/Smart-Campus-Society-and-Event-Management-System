-- Profiles Table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT,
  role TEXT CHECK (role IN ('student', 'society_head', 'admin')) DEFAULT 'student',
  department TEXT,
  interests TEXT, -- Comma separated or JSON, simple TEXT for MVP
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Society Table
CREATE TABLE IF NOT EXISTS societies (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT,
  department TEXT,
  head_id UUID REFERENCES profiles(id),
  logo TEXT,
  status TEXT DEFAULT 'active',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Event Categories
CREATE TABLE IF NOT EXISTS event_categories (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

-- Events Table
CREATE TABLE IF NOT EXISTS events (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  society_id UUID REFERENCES societies(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  description TEXT,
  category TEXT,
  date DATE,
  start_time TIME,
  end_time TIME,
  venue TEXT,
  capacity INTEGER,
  fee DECIMAL,
  is_paid BOOLEAN DEFAULT false,
  status TEXT DEFAULT 'pending', -- pending, approved, rejected
  poster TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Registrations Table
CREATE TABLE IF NOT EXISTS registrations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  event_id UUID REFERENCES events(id) ON DELETE CASCADE,
  student_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  payment_status TEXT DEFAULT 'unpaid', -- unpaid, paid
  registration_status TEXT DEFAULT 'confirmed', -- confirmed, cancelled
  qr_token TEXT UNIQUE,
  registered_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Attendance Table
CREATE TABLE IF NOT EXISTS attendance (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  registration_id UUID REFERENCES registrations(id) ON DELETE CASCADE UNIQUE,
  status TEXT DEFAULT 'attended',
  scanned_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Insert some default categories
INSERT INTO event_categories (name) VALUES 
  ('Technology'),
  ('Science'),
  ('Arts'),
  ('Sports'),
  ('Business'),
  ('General')
ON CONFLICT (name) DO NOTHING;

-- Trigger to automatically create a profile entry when a new auth user signs up
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email, name, role)
  values (new.id, new.email, coalesce(new.raw_user_meta_data->>'name', 'New User'), coalesce(new.raw_user_meta_data->>'role', 'student'))
  on conflict (id) do nothing;
  return new;
end;
$$;

-- Trigger on auth.users (Drop first if exists to be safe)
drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
