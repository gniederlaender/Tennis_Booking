-- Migration: Add availability snapshots table and newsletter fields to users table
-- Created: 2026-04-07

-- Create availability_snapshots table
CREATE TABLE IF NOT EXISTS availability_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    captured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location TEXT NOT NULL,  -- 'arsenal' or 'postsv'
    weekday INTEGER NOT NULL,  -- 0=Monday to 6=Sunday
    timeblock TEXT NOT NULL,  -- 'morning', 'midday', 'evening'
    available_slots INTEGER NOT NULL DEFAULT 0
);

-- Create index for efficient querying
CREATE INDEX IF NOT EXISTS idx_snapshots_location_weekday_timeblock
    ON availability_snapshots(location, weekday, timeblock);
CREATE INDEX IF NOT EXISTS idx_snapshots_captured_at
    ON availability_snapshots(captured_at);

-- Add newsletter fields to users table
-- Note: SQLite doesn't support ADD COLUMN IF NOT EXISTS, so we handle this in Python migration
