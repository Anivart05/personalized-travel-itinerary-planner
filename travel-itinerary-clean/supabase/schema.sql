-- ====================================================================
-- Personalized Travel Itinerary Planner - Supabase Database Schema
-- ====================================================================

-- 1. Enable UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Users Table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 3. Trips Table (JSONB format preserves full day-by-day nested schedule)
CREATE TABLE IF NOT EXISTS public.trips (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    destination TEXT NOT NULL,
    country TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    duration_days INTEGER NOT NULL,
    travel_style TEXT NOT NULL,
    group_size INTEGER NOT NULL DEFAULT 1,
    budget_tier TEXT NOT NULL,
    trip_data JSONB NOT NULL,
    share_token TEXT UNIQUE,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 4. Indexes for fast retrieval
CREATE INDEX IF NOT EXISTS idx_trips_user_id ON public.trips(user_id);
CREATE INDEX IF NOT EXISTS idx_trips_destination ON public.trips(destination);
CREATE INDEX IF NOT EXISTS idx_trips_share_token ON public.trips(share_token);
CREATE INDEX IF NOT EXISTS idx_trips_created_at ON public.trips(created_at DESC);

-- 5. Row Level Security (RLS) Policies
ALTER TABLE public.trips ENABLE ROW LEVEL SECURITY;

-- Allow public read access if accessed via share token
CREATE POLICY "Public read access for shared trips"
    ON public.trips
    FOR SELECT
    USING (share_token IS NOT NULL);

-- Allow authenticated users to manage their own trips
CREATE POLICY "Users can manage their own trips"
    ON public.trips
    FOR ALL
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Allow service role or backend API full access
CREATE POLICY "Service role full access"
    ON public.trips
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
