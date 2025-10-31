# Implementation Plan

- [x] 1. Add cleanup configuration to Config class
  - Add CLEANUP_ENABLED, CLEANUP_RETENTION_DAYS, CLEANUP_RETENTION_COUNT, and CLEANUP_RETENTION_MODE constants to config.py
  - Set sensible defaults (enabled=true, 7 days, 3 runs, hybrid mode)
  - _Requirements: 2.1, 2.2, 2.3, 2.4_

- [x] 2. Create DBCleanupManager class with core utilities
  - [x] 2.1 Create db_cleanup.py file with DBCleanupManager class skeleton
    - Implement __init__ method accepting base_db_dir and current_run_id
    - Store configuration from Config class
    - _Requirements: 1.1, 4.2_
  
  - [x] 2.2 Implement get_all_runs() method
    - Scan BASE_DB_DIR for folders matching run_YYYYMMDD_HHMMSS pattern
    - Parse timestamps from folder names
    - Return list of run info dictionaries with path, run_id, created_time, age_days
    - Skip folders that don't match expected pattern
    - _Requirements: 1.1, 4.4_
  
  - [x] 2.3 Implement calculate_folder_size() method
    - Use os.walk() to traverse folder structure
    - Sum file sizes to get total bytes
    - Handle symlinks safely (skip or follow based on safety)
    - Return size in bytes
    - _Requirements: 5.2_
  
  - [x] 2.4 Implement _format_bytes() helper method
    - Convert bytes to human-readable format (KB, MB, GB)
    - Return formatted string
    - _Requirements: 5.1, 5.2_

- [x] 3. Implement retention policy logic
  - [x] 3.1 Implement should_delete_run() method
    - Check if run is current run (never delete)
    - Apply retention policy based on CLEANUP_RETENTION_MODE
    - For "days" mode: check if age_days > CLEANUP_RETENTION_DAYS
    - For "count" mode: check if run is beyond top N runs
    - For "hybrid" mode: keep if either condition is satisfied
    - Return boolean decision
    - _Requirements: 2.1, 2.2, 2.3, 4.2_
  
  - [x] 3.2 Implement _get_runs_to_keep_by_count() helper method
    - Sort runs by created_time (newest first)
    - Return set of run_ids for the N most recent runs
    - _Requirements: 2.1_

- [x] 4. Implement cleanup execution
  - [x] 4.1 Implement cleanup_old_runs() method
    - Get all runs using get_all_runs()
    - Calculate size for each run
    - Determine which runs to delete using should_delete_run()
    - If dry_run=True, return what would be deleted without deleting
    - Delete folders using shutil.rmtree()
    - Track deleted_count, space_freed_bytes, and errors
    - Return cleanup result dictionary
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.3_
  
  - [x] 4.2 Add error handling for deletion failures
    - Wrap shutil.rmtree() in try-except
    - Catch OSError for permission denied and folder in use
    - Log errors and continue with remaining folders
    - Collect errors in result dictionary
    - _Requirements: 1.5, 4.1, 4.3_

- [x] 5. Implement storage statistics
  - [x] 5.1 Implement get_storage_stats() method
    - Get all runs with metadata
    - Calculate size for each run
    - Calculate total size across all runs
    - Format sizes to human-readable strings
    - Mark current run in the list
    - Return storage statistics dictionary
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 6. Implement manual cleanup interface
  - [x] 6.1 Implement manual_cleanup() method
    - Get storage stats using get_storage_stats()
    - Display runs with age and size
    - If delete_all=True, mark all non-current runs for deletion
    - Otherwise, apply retention policy
    - Show what will be deleted
    - Request user confirmation (y/n)
    - If confirmed, call cleanup_old_runs()
    - Return cleanup results
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 7. Integrate automatic cleanup into VectorStore
  - [x] 7.1 Update VectorStore.__init__() method
    - Import DBCleanupManager at the top of vector_store.py
    - Before ensure_db_path_exists(), check if Config.CLEANUP_ENABLED
    - If enabled, create DBCleanupManager instance
    - Call cleanup_old_runs() and capture result
    - If deleted_count > 0, print cleanup summary with space freed
    - _Requirements: 1.1, 1.3, 1.4_

- [x] 8. Add CLI commands for manual cleanup
  - [x] 8.1 Add --cleanup argument to main.py
    - Add argument to parser with help text
    - Implement handler that creates DBCleanupManager
    - Call manual_cleanup() method
    - Display results to user
    - _Requirements: 3.1, 3.2, 3.4, 3.5_
  
  - [x] 8.2 Add --cleanup-all argument to main.py
    - Add argument to parser with help text
    - Implement handler that creates DBCleanupManager
    - Call manual_cleanup(delete_all=True)
    - Display results to user
    - _Requirements: 3.3, 3.4, 3.5_
  
  - [x] 8.3 Add --storage-stats argument to main.py
    - Add argument to parser with help text
    - Implement handler that creates DBCleanupManager
    - Call get_storage_stats()
    - Format and display statistics in a readable table format
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [x] 9. Update .gitignore for cleanup
  - Ensure chroma_db_runs/ is in .gitignore (already present as chroma_db/)
  - Update pattern to chroma_db_runs/ if needed
  - _Requirements: N/A (housekeeping)_

- [x] 10. Add documentation
  - [x] 10.1 Update README or create CLEANUP.md
    - Document cleanup configuration options
    - Explain retention modes (days, count, hybrid)
    - Provide examples of CLI commands
    - Explain automatic vs manual cleanup
    - _Requirements: All (documentation)_
