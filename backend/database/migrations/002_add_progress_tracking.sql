-- Add progress tracking to jobs table
-- This allows real-time updates of analysis progress

ALTER TABLE jobs ADD COLUMN IF NOT EXISTS progress_data JSONB DEFAULT '{"stage": "pending", "current_agent": null, "agents_completed": [], "started_at": null, "estimated_completion": null}'::jsonb;

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_jobs_progress ON jobs USING gin(progress_data);

-- Example progress_data structure:
-- {
--   "stage": "running",              // "pending", "running", "completed", "failed"
--   "current_agent": "reporter",     // null, "planner", "reporter", "charter", "retirement"
--   "agents_completed": ["planner"], // List of completed agents
--   "started_at": "2025-11-26T21:52:19Z",
--   "agent_timings": {               // Actual execution times
--     "planner": 7,
--     "reporter": 33,
--     "charter": 22,
--     "retirement": 17
--   },
--   "estimated_completion": "2025-11-26T21:53:39Z",
--   "progress_percent": 45           // 0-100
-- }
