# Requirements Document

## Introduction

This feature adds a cleanup mechanism to manage ChromaDB run folders that accumulate over time. Currently, each application run creates a new timestamped database folder in `chroma_db_runs/`, leading to storage bloat. This feature will provide automated and manual cleanup options to maintain only relevant database runs while preserving the current active run.

## Requirements

### Requirement 1: Automatic Cleanup on Startup

**User Story:** As a user, I want old database runs to be automatically cleaned up when I start the application, so that I don't have to manually manage storage.

#### Acceptance Criteria

1. WHEN the application initializes THEN the system SHALL check for database runs older than a configurable retention period
2. WHEN old runs are detected THEN the system SHALL delete folders older than the retention period
3. WHEN cleanup occurs THEN the system SHALL preserve the current run being created
4. WHEN cleanup completes THEN the system SHALL log the number of runs deleted and space freed
5. IF cleanup fails for a specific folder THEN the system SHALL continue with other folders and log the error

### Requirement 2: Configurable Retention Policy

**User Story:** As a user, I want to configure how long database runs are kept, so that I can balance storage usage with my needs.

#### Acceptance Criteria

1. WHEN configuring retention THEN the system SHALL support retention by number of runs (e.g., keep last 5 runs)
2. WHEN configuring retention THEN the system SHALL support retention by age (e.g., keep runs from last 7 days)
3. WHEN no configuration is provided THEN the system SHALL use sensible defaults (keep last 3 runs OR 7 days, whichever is more)
4. WHEN retention is set to 0 or negative THEN the system SHALL disable automatic cleanup

### Requirement 3: Manual Cleanup Command

**User Story:** As a user, I want to manually trigger cleanup of old runs, so that I can free up space on demand.

#### Acceptance Criteria

1. WHEN user runs cleanup command THEN the system SHALL list all available runs with their age and size
2. WHEN user confirms cleanup THEN the system SHALL delete runs according to retention policy
3. WHEN user runs cleanup with --all flag THEN the system SHALL delete all runs except the current one
4. WHEN cleanup is triggered THEN the system SHALL require user confirmation before deletion
5. WHEN cleanup completes THEN the system SHALL display summary of deleted runs and space freed

### Requirement 4: Safe Deletion

**User Story:** As a developer, I want the cleanup mechanism to safely handle edge cases, so that active databases are never corrupted or deleted.

#### Acceptance Criteria

1. WHEN a run folder is being used by another process THEN the system SHALL skip that folder and log a warning
2. WHEN the current run folder is encountered THEN the system SHALL never delete it
3. WHEN deletion fails THEN the system SHALL log the error and continue with other folders
4. WHEN a folder doesn't match the expected naming pattern THEN the system SHALL skip it

### Requirement 5: Storage Statistics

**User Story:** As a user, I want to see storage usage statistics for database runs, so that I can understand my storage consumption.

#### Acceptance Criteria

1. WHEN user requests storage stats THEN the system SHALL display total size of all runs
2. WHEN displaying stats THEN the system SHALL show size per run folder
3. WHEN displaying stats THEN the system SHALL show age of each run
4. WHEN displaying stats THEN the system SHALL show which run is currently active
