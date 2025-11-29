# How to Completely Remove Progress Tracking

If you decide to remove progress tracking entirely, follow these steps:

## Option 1: Leave Code, Keep Disabled (Recommended)

**Easiest approach** - just keep `ENABLE_PROGRESS_TRACKING=false` (the default).

- No changes needed
- Code stays but does nothing
- Zero performance impact
- Can re-enable anytime

## Option 2: Remove Code Completely

### Step 1: Revert Backend Files

Delete or revert these files:

```bash
cd backend/planner

# Remove progress tracking module
rm progress.py
rm PROGRESS_TRACKING_README.md
rm REMOVE_PROGRESS_TRACKING.md
```

### Step 2: Revert agent.py

Remove these sections from `backend/planner/agent.py`:

1. **Import statement** (line ~15):
```python
from progress import ProgressTracker  # DELETE THIS LINE
```

2. **PlannerContext dataclass** (revert to original):
```python
@dataclass
class PlannerContext:
    """Context for planner agent tools."""
    job_id: str
    # REMOVE these two lines:
    # progress: ProgressTracker
    # agents_completed: List[str]
```

3. **create_agent function** (revert progress initialization):
```python
def create_agent(job_id: str, portfolio_summary: Dict[str, Any], db):
    """Create the orchestrator agent with tools."""

    # REMOVE these lines:
    # # Initialize progress tracker
    # progress = ProgressTracker(job_id, db)

    # Revert context creation to:
    context = PlannerContext(job_id=job_id)
```

4. **Tool functions** (revert all three):

**invoke_reporter:**
```python
@function_tool
async def invoke_reporter(wrapper: RunContextWrapper[PlannerContext]) -> str:
    """Invoke the Report Writer agent to generate portfolio analysis narrative."""
    # REMOVE progress tracking lines:
    # wrapper.context.progress.start_agent("reporter")
    result = await invoke_reporter_internal(wrapper.context.job_id)
    # wrapper.context.agents_completed.append("reporter")
    # wrapper.context.progress.complete_agent("reporter", wrapper.context.agents_completed)
    return result
```

**invoke_charter:**
```python
@function_tool
async def invoke_charter(wrapper: RunContextWrapper[PlannerContext]) -> str:
    """Invoke the Chart Maker agent to create portfolio visualizations."""
    # REMOVE progress tracking lines
    result = await invoke_charter_internal(wrapper.context.job_id)
    return result
```

**invoke_retirement:**
```python
@function_tool
async def invoke_retirement(wrapper: RunContextWrapper[PlannerContext]) -> str:
    """Invoke the Retirement Specialist agent for retirement projections."""
    # REMOVE progress tracking lines
    result = await invoke_retirement_internal(wrapper.context.job_id)
    return result
```

### Step 3: Revert lambda_handler.py

Remove these sections from `backend/planner/lambda_handler.py`:

```python
async def run_orchestrator(job_id: str) -> None:
    """Run the orchestrator agent to coordinate portfolio analysis."""
    try:
        # ... existing code ...

        # Create agent with tools and context
        model, tools, task, context = create_agent(job_id, portfolio_summary, db)

        # REMOVE this line:
        # context.progress.start()

        # Run the orchestrator
        with trace("Planner Orchestrator"):
            # ... existing code ...

            # REMOVE this line:
            # context.progress.complete()
            db.jobs.update_status(job_id, "completed")

    except Exception as e:
        logger.error(f"Planner: Error in orchestration: {e}", exc_info=True)
        # REMOVE this block:
        # try:
        #     if 'context' in locals() and hasattr(context, 'progress'):
        #         context.progress.fail(str(e))
        # except:
        #     pass
        db.jobs.update_status(job_id, 'failed', error_message=str(e))
        raise
```

### Step 4: (Optional) Remove Database Column

If you want to remove the `progress_data` column entirely:

```sql
ALTER TABLE jobs DROP COLUMN IF EXISTS progress_data;
DROP INDEX IF EXISTS idx_jobs_progress;
```

**WARNING:** Only do this if you're certain you won't use progress tracking in the future.

### Step 5: Redeploy

```bash
# Package and deploy updated Lambda
cd backend/planner
uv run package_docker.py

# Deploy with Terraform
cd ../../terraform/6_agents
terraform apply
```

## Verification

After removal:

```bash
# Check logs - should NOT see progress messages
aws logs tail /aws/lambda/alex-planner --follow | grep -i progress

# Run an analysis - should work exactly as before
cd backend/planner
uv run pytest test_simple.py -v
```

## Comparison: Disable vs Remove

| Aspect | Disable (Recommended) | Remove Completely |
|--------|----------------------|-------------------|
| Effort | None (default state) | Revert 4 files |
| Risk | Zero | Medium (merge conflicts) |
| Reversible | Instant (flip flag) | Requires code restore |
| Performance | Identical to removal | Identical to disable |
| Maintenance | Low | None |

**Recommendation:** Just keep it disabled. The code is clean, feature-flagged, and has zero impact when disabled.

## Questions?

If unsure, keep the code with `ENABLE_PROGRESS_TRACKING=false` (default). You can always enable it later if needed.
