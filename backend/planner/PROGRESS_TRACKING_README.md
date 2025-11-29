# Progress Tracking Feature Flag

## Overview

Real-time progress tracking is **OPTIONAL** and controlled via environment variable.

## How to Enable/Disable

### Enable Progress Tracking

Set environment variable:
```bash
ENABLE_PROGRESS_TRACKING=true
```

### Disable Progress Tracking (DEFAULT)

Progress tracking is **DISABLED by default**. To explicitly disable:
```bash
ENABLE_PROGRESS_TRACKING=false
```

Or simply don't set the variable at all.

## Deployment

### AWS Lambda Environment Variables

**To enable in deployed Lambda:**

1. Via Terraform (recommended):
```hcl
# In terraform/6_agents/main.tf
environment {
  variables = {
    ENABLE_PROGRESS_TRACKING = "true"  # or "false"
    # ... other variables
  }
}
```

2. Via AWS Console:
   - Go to Lambda function: `alex-planner`
   - Configuration → Environment variables
   - Add: `ENABLE_PROGRESS_TRACKING` = `true`

3. Via AWS CLI:
```bash
aws lambda update-function-configuration \
  --function-name alex-planner \
  --environment "Variables={ENABLE_PROGRESS_TRACKING=true,...}"
```

### Local Testing

**In your `.env` file:**
```bash
# Enable progress tracking
ENABLE_PROGRESS_TRACKING=true

# Disable progress tracking
ENABLE_PROGRESS_TRACKING=false
```

## Testing

### Test with Feature ENABLED
```bash
# Set environment variable
export ENABLE_PROGRESS_TRACKING=true

# Run test
cd backend/planner
uv run pytest test_simple.py -v
```

### Test with Feature DISABLED
```bash
# Unset or set to false
export ENABLE_PROGRESS_TRACKING=false

# Run test
cd backend/planner
uv run pytest test_simple.py -v
```

## How It Works

**When ENABLED:**
- Progress updates written to `jobs.progress_data` field
- Real-time tracking of agent execution
- Progress percentages calculated
- Estimated completion times provided
- Logs show: "Progress: Updated to X% - message"

**When DISABLED:**
- All progress tracking calls become no-ops
- No database writes for progress_data
- System behaves exactly as before
- Logs show: "Progress tracking is DISABLED via feature flag"
- **Zero performance impact**

## Database Impact

**When DISABLED:**
- `progress_data` field remains NULL in jobs table
- No extra database writes
- No performance overhead

**When ENABLED:**
- `progress_data` field updated ~5-6 times per analysis:
  1. Start (setup)
  2. Reporter start
  3. Reporter complete
  4. Charter start
  5. Charter complete
  6. Retirement start
  7. Retirement complete
  8. Analysis complete

## Rollback Plan

If issues arise:

1. **Quick disable:** Set `ENABLE_PROGRESS_TRACKING=false` in Lambda environment
2. **Verify:** Check logs for "Progress tracking is DISABLED"
3. **Confirm:** System works exactly as before

## Migration Path

**Phase 1:** Deploy with feature DISABLED (default)
```bash
# No environment variable needed
# System behaves exactly as before
```

**Phase 2:** Enable on staging/test
```bash
ENABLE_PROGRESS_TRACKING=true
# Test thoroughly
```

**Phase 3:** Enable in production
```bash
# Update Lambda environment variable
ENABLE_PROGRESS_TRACKING=true
# Monitor CloudWatch logs
```

**Phase 4:** Update frontend to display progress
```bash
# Only after backend is stable
```

## Monitoring

**Check if enabled:**
```bash
# View Lambda environment variables
aws lambda get-function-configuration \
  --function-name alex-planner \
  --query 'Environment.Variables.ENABLE_PROGRESS_TRACKING'
```

**Check logs:**
```bash
# If disabled, you'll see:
aws logs tail /aws/lambda/alex-planner --format short | grep "Progress tracking is DISABLED"

# If enabled, you'll see:
aws logs tail /aws/lambda/alex-planner --format short | grep "Progress: Updated to"
```

## Performance Notes

- **Disabled:** Zero overhead, identical to original code
- **Enabled:** ~5-6 extra database UPDATE operations per analysis
  - Minimal impact: <100ms total overhead
  - Updates are non-blocking
  - No impact on agent execution time

## Support

If something goes wrong:
1. Disable the feature flag immediately
2. Check CloudWatch logs for errors
3. Verify database migrations ran successfully
4. Test locally with feature enabled to reproduce issue
