# Database Cleanup Documentation

## Overview

The YouTube RAG Chatbot creates a new ChromaDB database folder for each run, timestamped as `chroma_db_runs/run_YYYYMMDD_HHMMSS`. Over time, these folders can accumulate and consume significant disk space. The cleanup mechanism automatically manages these old runs based on configurable retention policies.

## Features

- **Automatic Cleanup**: Runs on application startup (configurable)
- **Manual Cleanup**: CLI commands for on-demand cleanup
- **Flexible Retention**: Keep runs by age, count, or hybrid mode
- **Safe Deletion**: Current run is always protected
- **Storage Statistics**: View disk usage across all runs

## Configuration

Configure cleanup behavior via environment variables in your `.env` file:

```bash
# Enable/disable automatic cleanup (default: true)
CLEANUP_ENABLED=true

# Keep runs from last N days (default: 7)
CLEANUP_RETENTION_DAYS=7

# Keep last N runs (default: 3)
CLEANUP_RETENTION_COUNT=3

# Retention mode: "days", "count", or "hybrid" (default: hybrid)
CLEANUP_RETENTION_MODE=hybrid
```

### Retention Modes

- **`days`**: Keep only runs from the last N days
- **`count`**: Keep only the last N runs (by creation time)
- **`hybrid`**: Keep runs that satisfy EITHER condition (more permissive)

**Example with hybrid mode (default):**
- `CLEANUP_RETENTION_DAYS=7`
- `CLEANUP_RETENTION_COUNT=3`
- Result: Keeps runs from last 7 days OR the 3 most recent runs, whichever includes more

## Automatic Cleanup

Automatic cleanup runs when the application starts (when `VectorStore` is initialized). It:

1. Scans `chroma_db_runs/` for old run folders
2. Applies retention policy to determine what to delete
3. Deletes old runs and reports space freed
4. Protects the current run from deletion

**Example output:**
```
🧹 Cleaned up 5 old run(s) (127.3 MB freed)
```

To disable automatic cleanup:
```bash
CLEANUP_ENABLED=false
```

## Manual Cleanup Commands

### View Storage Statistics

See disk usage across all database runs:

```bash
python main.py --storage-stats
```

**Example output:**
```
================================================================================
DATABASE STORAGE STATISTICS
================================================================================

📊 Total Runs: 8
💾 Total Size: 245.6 MB
🔄 Current Run: 20251030_143022

Runs:
--------------------------------------------------------------------------------
  20251030_143022 |    15.2 MB |     0.0 days ago ⭐ CURRENT
  20251029_091544 |    32.1 MB |     1.2 days ago
  20251028_192349 |    28.5 MB |     1.9 days ago
  20251027_154211 |    41.3 MB |     2.8 days ago
  20251026_103045 |    19.7 MB |     3.9 days ago
  20251025_081522 |    35.4 MB |     4.9 days ago
  20251024_173308 |    42.8 MB |     5.8 days ago
  20251023_120156 |    30.6 MB |     6.9 days ago
--------------------------------------------------------------------------------

================================================================================
```

### Clean Up Old Runs

Clean up runs according to retention policy:

```bash
python main.py --cleanup
```

This will:
1. Show what will be deleted
2. Display space to be freed
3. Ask for confirmation
4. Delete confirmed runs

**Example interaction:**
```
================================================================================
DATABASE CLEANUP
================================================================================

📊 Total Runs: 8
💾 Total Size: 245.6 MB
🔄 Current Run: 20251030_143022

Runs:
--------------------------------------------------------------------------------
  20251030_143022 |    15.2 MB |     0.0 days ago ⭐ CURRENT
  20251029_091544 |    32.1 MB |     1.2 days ago
  ...
--------------------------------------------------------------------------------

Retention Policy: hybrid
  - Keep runs from last 7 days
  - Keep last 3 runs

Will delete 5 run(s):
  - 20251023_120156
  - 20251024_173308
  - 20251025_081522
  - 20251026_103045
  - 20251027_154211

Space to be freed: 169.8 MB

Proceed with deletion? (y/n): y

🧹 Cleaning up...

   Deleted: 20251023_120156 (30.6 MB)
   Deleted: 20251024_173308 (42.8 MB)
   Deleted: 20251025_081522 (35.4 MB)
   Deleted: 20251026_103045 (19.7 MB)
   Deleted: 20251027_154211 (41.3 MB)

✅ Cleanup complete!
   Deleted: 5 run(s)
   Space freed: 169.8 MB

================================================================================
```

### Delete All Old Runs

Delete all runs except the current one:

```bash
python main.py --cleanup-all
```

This ignores retention policy and deletes everything except the active run. Requires confirmation.

## Safety Features

1. **Current Run Protection**: The active run is never deleted
2. **Confirmation Required**: Manual cleanup requires explicit user confirmation
3. **Error Handling**: If a folder can't be deleted (permissions, in use), it's skipped and logged
4. **Dry Run Preview**: Shows what will be deleted before actual deletion

## Troubleshooting

### Cleanup Not Running

Check if cleanup is enabled:
```bash
# In .env file
CLEANUP_ENABLED=true
```

### Permission Errors

If you see permission errors during cleanup:
```
⚠️ Failed to delete run_20251020_120000: Permission denied
```

This usually means:
- The folder is in use by another process
- Insufficient file system permissions

The cleanup will skip that folder and continue with others.

### No Runs Deleted

If cleanup reports 0 deletions, all runs are within retention policy. Check your settings:
- Increase `CLEANUP_RETENTION_DAYS` to keep fewer days
- Decrease `CLEANUP_RETENTION_COUNT` to keep fewer runs
- Change mode from `hybrid` to `days` or `count` for stricter retention

## Best Practices

1. **Development**: Use `hybrid` mode with generous retention (7 days, 3 runs)
2. **Production**: Use `days` mode with shorter retention (3 days)
3. **Storage-Constrained**: Use `count` mode to keep only last 1-2 runs
4. **Disable for Testing**: Set `CLEANUP_ENABLED=false` when debugging

## Examples

### Keep Only Last 2 Runs
```bash
CLEANUP_ENABLED=true
CLEANUP_RETENTION_COUNT=2
CLEANUP_RETENTION_MODE=count
```

### Keep Only Last 3 Days
```bash
CLEANUP_ENABLED=true
CLEANUP_RETENTION_DAYS=3
CLEANUP_RETENTION_MODE=days
```

### Aggressive Cleanup (Last Run Only)
```bash
CLEANUP_ENABLED=true
CLEANUP_RETENTION_COUNT=1
CLEANUP_RETENTION_MODE=count
```

### Disable Automatic Cleanup
```bash
CLEANUP_ENABLED=false
```

Then use manual cleanup when needed:
```bash
python main.py --cleanup
```
