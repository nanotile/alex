"""
Progress tracking helper for real-time analysis updates

FEATURE FLAG: Set ENABLE_PROGRESS_TRACKING=true to enable real-time progress updates
"""

import os
import time
import logging
from typing import Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger()

# Feature flag - can be disabled via environment variable
ENABLE_PROGRESS_TRACKING = os.getenv("ENABLE_PROGRESS_TRACKING", "false").lower() == "true"

# Average timing from real data
AGENT_TIMINGS = {
    "setup": 7,
    "reporter": 33,
    "charter": 22,
    "retirement": 17
}

TOTAL_TIME = sum(AGENT_TIMINGS.values())  # ~79 seconds


class ProgressTracker:
    """Track and update analysis progress in real-time (optional via feature flag)"""

    def __init__(self, job_id: str, db, enabled: bool = None):
        self.job_id = job_id
        self.db = db
        self.enabled = enabled if enabled is not None else ENABLE_PROGRESS_TRACKING
        self.start_time = None
        self.agent_start_times = {}

        if not self.enabled:
            logger.info("Progress tracking is DISABLED via feature flag")

    def start(self):
        """Mark analysis as started"""
        if not self.enabled:
            return

        self.start_time = time.time()
        self._update_progress(
            stage="running",
            current_agent="setup",
            progress_percent=0,
            message="Starting analysis..."
        )

    def start_agent(self, agent_name: str):
        """Mark an agent as started"""
        if not self.enabled:
            return

        self.agent_start_times[agent_name] = time.time()

        # Calculate progress based on completed agents
        completed_time = sum(
            AGENT_TIMINGS.get(agent, 0)
            for agent in self.agent_start_times.keys()
            if agent in AGENT_TIMINGS and agent != agent_name
        )
        progress_percent = int((completed_time / TOTAL_TIME) * 100)

        # Estimate completion time
        remaining_time = TOTAL_TIME - completed_time
        estimated_completion = datetime.now() + timedelta(seconds=remaining_time)

        self._update_progress(
            stage="running",
            current_agent=agent_name,
            progress_percent=min(progress_percent, 95),  # Never show 100% until done
            estimated_completion=estimated_completion.isoformat(),
            message=f"Running {agent_name.title()} Agent..."
        )

    def complete_agent(self, agent_name: str, agents_completed: List[str]):
        """Mark an agent as completed"""
        if not self.enabled:
            return

        if agent_name in self.agent_start_times:
            elapsed = time.time() - self.agent_start_times[agent_name]
            logger.info(f"Progress: {agent_name} completed in {elapsed:.1f}s")

            # Calculate overall progress
            completed_time = sum(
                AGENT_TIMINGS.get(agent, 0)
                for agent in agents_completed
            )
            progress_percent = int((completed_time / TOTAL_TIME) * 100)

            self._update_progress(
                stage="running",
                current_agent=None,
                progress_percent=min(progress_percent, 95),
                agents_completed=agents_completed,
                message=f"{agent_name.title()} completed"
            )

    def complete(self):
        """Mark analysis as completed"""
        if not self.enabled:
            return

        total_elapsed = time.time() - self.start_time if self.start_time else 0
        logger.info(f"Progress: Analysis completed in {total_elapsed:.1f}s")

        self._update_progress(
            stage="completed",
            current_agent=None,
            progress_percent=100,
            message="Analysis complete!"
        )

    def fail(self, error_message: str):
        """Mark analysis as failed"""
        if not self.enabled:
            return

        self._update_progress(
            stage="failed",
            current_agent=None,
            message=f"Analysis failed: {error_message}"
        )

    def _update_progress(
        self,
        stage: str,
        current_agent: Optional[str] = None,
        progress_percent: int = 0,
        agents_completed: Optional[List[str]] = None,
        estimated_completion: Optional[str] = None,
        message: str = ""
    ):
        """Update progress_data in the database"""
        progress_data = {
            "stage": stage,
            "current_agent": current_agent,
            "progress_percent": progress_percent,
            "agents_completed": agents_completed or [],
            "message": message,
            "updated_at": datetime.now().isoformat()
        }

        if estimated_completion:
            progress_data["estimated_completion"] = estimated_completion

        # Update the jobs table using the db.jobs.update method
        try:
            self.db.jobs.update(
                self.job_id,
                {"progress_data": progress_data}
            )
            logger.info(f"Progress: Updated to {progress_percent}% - {message}")
        except Exception as e:
            logger.error(f"Progress: Failed to update progress: {e}")
