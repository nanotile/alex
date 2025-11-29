# Real-Time Debugging & Status Reporting - Implementation Plan

## Problem Statement

Current progress tracking is cosmetic and provides no useful operational data:
- ❌ Shows "Status: running" with no details
- ❌ "Elapsed time" shows total time, not per-agent timing
- ❌ No indication of which agent is actually executing
- ❌ Job completes but frontend never shows completion
- ❌ No way to debug slow agents or identify bottlenecks

## Requirements

Users need **operational intelligence**:
- ✅ Which agent is currently executing
- ✅ How long each agent took to complete
- ✅ Report generation time (how long to create the markdown)
- ✅ Clear completion notification
- ✅ Actual error messages with context
- ✅ Debugging data: CloudWatch log links, Lambda execution IDs

## Architecture Changes

### Backend Changes (Planner Lambda)

**File**: `backend/planner/agent.py`

Add timing instrumentation to agent tool wrappers:

```python
import time
from contextlib import contextmanager

@contextmanager
def track_agent_execution(agent_name: str, context):
    """Context manager to track agent execution time."""
    start_time = time.time()
    logger.info(f"{agent_name}: Starting execution")

    try:
        yield

        duration = time.time() - start_time
        logger.info(f"{agent_name}: Completed in {duration:.2f}s")

        # Store timing in job metadata
        if hasattr(context, 'execution_times'):
            context.execution_times[agent_name.lower()] = {
                'start': start_time,
                'duration': duration,
                'status': 'completed'
            }
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"{agent_name}: Failed after {duration:.2f}s: {e}")

        if hasattr(context, 'execution_times'):
            context.execution_times[agent_name.lower()] = {
                'start': start_time,
                'duration': duration,
                'status': 'failed',
                'error': str(e)
            }
        raise
```

Wrap each agent invocation:

```python
@function_tool
async def analyze_portfolio(wrapper: RunContextWrapper[PlannerContext]) -> str:
    """Analyze portfolio and generate comprehensive report."""
    context = wrapper.context

    with track_agent_execution("Reporter", context):
        # Invoke Reporter Lambda
        response = lambda_client.invoke(...)

        # Parse and store results
        result = json.loads(response['Payload'].read())

        # Update job with Reporter's output
        db.jobs.update_payload(context.job_id, 'report_payload', result)

        return f"Portfolio analysis complete. Generated {len(result.get('report', ''))} char report."
```

**File**: `backend/planner/lambda_handler.py`

Store execution summary in `summary_payload` before marking job as completed:

```python
async def run_orchestrator(job_id: str) -> None:
    """Run the orchestrator agent to coordinate portfolio analysis."""
    overall_start = time.time()
    execution_times = {}

    try:
        # ... existing code ...

        # Create context with execution tracking
        context = PlannerContext(
            job_id=job_id,
            db=db,
            portfolio_summary=portfolio_summary,
            progress=progress_tracker,
            execution_times=execution_times  # ADD THIS
        )

        # ... run agent ...

        # Calculate total execution time
        total_duration = time.time() - overall_start

        # Store execution summary
        summary = {
            'summary': 'Portfolio analysis completed',
            'total_duration_seconds': total_duration,
            'agent_executions': execution_times,
            'completion_time': datetime.now().isoformat(),
            'agents_invoked': list(execution_times.keys())
        }

        db.jobs.update_payload(job_id, 'summary_payload', summary)
        db.jobs.update_status(job_id, "completed")

        logger.info(f"Planner: Job {job_id} completed in {total_duration:.2f}s")

    except Exception as e:
        # ... error handling ...
```

### Frontend Changes

**File**: `frontend/components/AnalysisProgressTracker.tsx`

Replace cosmetic UI with **operational dashboard**:

```tsx
interface AgentExecution {
  agent: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  start_time?: string;
  duration?: number;
  error?: string;
}

interface JobDebugInfo {
  job_id: string;
  status: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  total_duration?: number;
  agent_executions?: Record<string, AgentExecution>;
  cloudwatch_log_group?: string;
  lambda_request_id?: string;
}

// Real-time display showing:
// 1. Overall job timeline (created → started → completed)
// 2. Agent execution table with actual timings
// 3. Current agent (if running)
// 4. Debug links (CloudWatch logs, Aurora query traces)
```

**Display Structure**:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                    PORTFOLIO ANALYSIS STATUS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Job ID: 3e5f8a9b-1234-5678-9abc-def012345678
Status: ✅ COMPLETED

Timeline:
  Created:   2025-11-28 14:00:00
  Started:   2025-11-28 14:00:02  (+2s)
  Completed: 2025-11-28 14:01:15  (+73s total)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                      AGENT EXECUTION DETAILS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Agent                    Status        Duration    Details
──────────────────────────────────────────────────────────
Tagger                   ✅ Completed   3.2s       Classified 12 instruments
Reporter                 ✅ Completed  28.5s       Generated 4,523 char report
Charter                  ✅ Completed  15.3s       Created 3 visualizations
Retirement               ✅ Completed  22.1s       Projected 30 years
Planner (Orchestrator)   ✅ Completed   4.2s       Coordination complete

Total Execution: 73.3 seconds

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                          DEBUG INFORMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CloudWatch Logs: [View Logs] → /aws/lambda/alex-planner
Lambda Request ID: abc123-def456-ghi789
Database Queries: 47 queries, 2.1s total

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Implementation Steps

### Phase 1: Backend Timing Capture (HIGH PRIORITY)
1. ✅ Add `execution_times` dict to PlannerContext
2. ✅ Wrap each agent tool call with `track_agent_execution()`
3. ✅ Store timing data in `summary_payload` before completion
4. ✅ Add `started_at` and `completed_at` timestamps to job record
5. ✅ Test with `test_full.py` to verify timing data is captured

### Phase 2: Frontend Real-Time Display (HIGH PRIORITY)
1. ✅ Modify `AnalysisProgressTracker.tsx` to display execution table
2. ✅ Show timeline: created → started → completed
3. ✅ Display per-agent duration in seconds
4. ✅ Show current executing agent (if status == 'running')
5. ✅ Add CloudWatch log links for debugging
6. ✅ Remove cosmetic icons and "Agent Activity" cards
7. ✅ Show clear "COMPLETED" banner when done

### Phase 3: Completion Notification (CRITICAL)
1. ✅ Ensure frontend detects `status === 'completed'`
2. ✅ Show completion banner immediately
3. ✅ Call `onComplete()` callback to reload dashboard
4. ✅ Stop polling after completion

### Phase 4: Error Debugging (IMPORTANT)
1. ✅ Display full error messages (not "Analysis failed")
2. ✅ Show which agent failed and why
3. ✅ Include CloudWatch log group and request ID
4. ✅ Add "Retry Analysis" button for failed jobs

## Testing Checklist

- [ ] Run portfolio analysis via frontend
- [ ] Verify execution times appear in real-time
- [ ] Confirm completion banner shows immediately
- [ ] Check CloudWatch log links work
- [ ] Test error scenario (simulate agent failure)
- [ ] Verify timing accuracy (compare with CloudWatch)
- [ ] Ensure no polling after completion

## Success Metrics

**Before:**
- ❌ No idea which agent is running
- ❌ No visibility into execution time
- ❌ No completion notification
- ❌ No debugging information

**After:**
- ✅ See exact agent execution times
- ✅ Know which agent is currently running
- ✅ Immediate completion notification
- ✅ Direct links to CloudWatch logs
- ✅ Can identify bottlenecks and optimize
- ✅ Useful for debugging production issues

## Files to Modify

### Backend
- `backend/planner/agent.py` - Add timing instrumentation
- `backend/planner/lambda_handler.py` - Store timing in summary_payload
- `backend/planner/templates.py` - (No changes needed)

### Frontend
- `frontend/components/AnalysisProgressTracker.tsx` - Complete rewrite
- `frontend/pages/dashboard.tsx` - (Minor: ensure onComplete works)

## Notes

- Current `progress.py` module can be **ignored** - it's disabled and not providing real data
- Database schema already has `started_at`, `completed_at` - use them!
- `summary_payload` is already JSONB - perfect for execution metadata
- Frontend already polls every 2s - keep that, just show real data

## Priority

**CRITICAL**: Users cannot debug slow analyses without this.
**URGENCY**: Implement Phase 1 & 2 immediately.
