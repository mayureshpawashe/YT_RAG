import os
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any
from config import Config


class DBCleanupManager:
    """Manage cleanup of old ChromaDB run folders"""
    
    def __init__(self, base_db_dir: str, current_run_id: str):
        """
        Initialize cleanup manager
        
        Args:
            base_db_dir: Path to chroma_db_runs directory
            current_run_id: Current run ID to protect from deletion
        """
        self.base_db_dir = base_db_dir
        self.current_run_id = current_run_id
        
        # Load configuration
        self.cleanup_enabled = Config.CLEANUP_ENABLED
        self.retention_days = Config.CLEANUP_RETENTION_DAYS
        self.retention_count = Config.CLEANUP_RETENTION_COUNT
        self.retention_mode = Config.CLEANUP_RETENTION_MODE
        
        print(f"🧹 DBCleanupManager initialized")
        print(f"   Mode: {self.retention_mode}")
        print(f"   Retention: {self.retention_days} days OR {self.retention_count} runs")

    def get_all_runs(self) -> List[Dict[str, Any]]:
        """
        Get list of all run folders with metadata
        
        Returns:
            List of dicts with: path, run_id, created_time, age_days, is_current
        """
        if not os.path.exists(self.base_db_dir):
            return []
        
        runs = []
        
        try:
            for folder_name in os.listdir(self.base_db_dir):
                folder_path = os.path.join(self.base_db_dir, folder_name)
                
                # Skip if not a directory
                if not os.path.isdir(folder_path):
                    continue
                
                # Parse run_YYYYMMDD_HHMMSS pattern
                if not folder_name.startswith("run_"):
                    continue
                
                run_id = folder_name[4:]  # Remove "run_" prefix
                
                # Parse timestamp
                try:
                    created_time = datetime.strptime(run_id, "%Y%m%d_%H%M%S")
                except ValueError:
                    # Invalid format, skip
                    continue
                
                # Calculate age
                age = datetime.now() - created_time
                age_days = age.total_seconds() / 86400  # Convert to days
                
                runs.append({
                    'path': folder_path,
                    'run_id': run_id,
                    'created_time': created_time,
                    'age_days': age_days,
                    'is_current': run_id == self.current_run_id
                })
        
        except Exception as e:
            print(f"⚠️ Error scanning runs directory: {e}")
            return []
        
        # Sort by created_time (newest first)
        runs.sort(key=lambda x: x['created_time'], reverse=True)
        
        return runs

    def calculate_folder_size(self, folder_path: str) -> int:
        """
        Calculate total size of folder in bytes
        
        Args:
            folder_path: Path to folder
            
        Returns:
            Size in bytes
        """
        total_size = 0
        
        try:
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    
                    # Skip symlinks to avoid following external data
                    if os.path.islink(file_path):
                        continue
                    
                    try:
                        total_size += os.path.getsize(file_path)
                    except (OSError, FileNotFoundError):
                        # File may have been deleted or inaccessible
                        continue
        
        except Exception as e:
            print(f"⚠️ Error calculating size for {folder_path}: {e}")
            return 0
        
        return total_size

    def _format_bytes(self, bytes_size: int) -> str:
        """
        Convert bytes to human-readable format
        
        Args:
            bytes_size: Size in bytes
            
        Returns:
            Formatted string (e.g., "15.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"

    def _get_runs_to_keep_by_count(self, runs: List[Dict[str, Any]]) -> set:
        """
        Get set of run_ids to keep based on count retention
        
        Args:
            runs: List of run info dicts (should be sorted newest first)
            
        Returns:
            Set of run_ids to keep
        """
        # Keep the N most recent runs
        runs_to_keep = set()
        for i, run in enumerate(runs):
            if i < self.retention_count:
                runs_to_keep.add(run['run_id'])
        
        return runs_to_keep

    def should_delete_run(self, run_info: dict, runs_to_keep_by_count: set = None) -> bool:
        """
        Determine if a run should be deleted based on retention policy
        
        Args:
            run_info: Run metadata dict
            runs_to_keep_by_count: Pre-calculated set of run_ids to keep by count
            
        Returns:
            True if should delete, False otherwise
        """
        # Never delete current run
        if run_info['is_current']:
            return False
        
        run_id = run_info['run_id']
        age_days = run_info['age_days']
        
        # Apply retention policy based on mode
        if self.retention_mode == "days":
            # Keep only if within retention days
            return age_days > self.retention_days
        
        elif self.retention_mode == "count":
            # Keep only if in top N runs
            return run_id not in runs_to_keep_by_count
        
        elif self.retention_mode == "hybrid":
            # Keep if EITHER condition is satisfied (more permissive)
            keep_by_days = age_days <= self.retention_days
            keep_by_count = run_id in runs_to_keep_by_count
            return not (keep_by_days or keep_by_count)
        
        else:
            # Unknown mode, don't delete
            print(f"⚠️ Unknown retention mode: {self.retention_mode}")
            return False

    def cleanup_old_runs(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Delete old runs according to retention policy
        
        Args:
            dry_run: If True, only report what would be deleted
            
        Returns:
            Dict with: deleted_count, space_freed_bytes, errors, deleted_runs
        """
        runs = self.get_all_runs()
        
        if not runs:
            return {
                'deleted_count': 0,
                'space_freed_bytes': 0,
                'errors': [],
                'deleted_runs': []
            }
        
        # Pre-calculate runs to keep by count (for efficiency)
        runs_to_keep_by_count = self._get_runs_to_keep_by_count(runs)
        
        deleted_count = 0
        space_freed = 0
        errors = []
        deleted_runs = []
        
        for run in runs:
            # Check if should delete
            if not self.should_delete_run(run, runs_to_keep_by_count):
                continue
            
            # Calculate size before deletion
            size = self.calculate_folder_size(run['path'])
            
            if dry_run:
                # Just report, don't delete
                deleted_count += 1
                space_freed += size
                deleted_runs.append(run['run_id'])
                continue
            
            # Attempt deletion with error handling
            try:
                shutil.rmtree(run['path'])
                deleted_count += 1
                space_freed += size
                deleted_runs.append(run['run_id'])
                print(f"   Deleted: {run['run_id']} ({self._format_bytes(size)})")
            
            except OSError as e:
                # Handle permission denied, folder in use, etc.
                error_msg = f"Failed to delete {run['run_id']}: {str(e)}"
                errors.append({
                    'run_id': run['run_id'],
                    'error': str(e)
                })
                print(f"   ⚠️ {error_msg}")
            
            except Exception as e:
                # Catch any other errors
                error_msg = f"Unexpected error deleting {run['run_id']}: {str(e)}"
                errors.append({
                    'run_id': run['run_id'],
                    'error': str(e)
                })
                print(f"   ⚠️ {error_msg}")
        
        return {
            'deleted_count': deleted_count,
            'space_freed_bytes': space_freed,
            'space_freed_human': self._format_bytes(space_freed),
            'errors': errors,
            'deleted_runs': deleted_runs
        }

    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics for all runs
        
        Returns:
            Dict with: total_runs, total_size_bytes, total_size_human, runs, current_run
        """
        runs = self.get_all_runs()
        
        if not runs:
            return {
                'total_runs': 0,
                'total_size_bytes': 0,
                'total_size_human': '0 B',
                'runs': [],
                'current_run': self.current_run_id
            }
        
        # Calculate size for each run
        total_size = 0
        for run in runs:
            size = self.calculate_folder_size(run['path'])
            run['size_bytes'] = size
            run['size_human'] = self._format_bytes(size)
            total_size += size
        
        return {
            'total_runs': len(runs),
            'total_size_bytes': total_size,
            'total_size_human': self._format_bytes(total_size),
            'runs': runs,
            'current_run': self.current_run_id
        }

    def manual_cleanup(self, delete_all: bool = False) -> Dict[str, Any]:
        """
        Interactive manual cleanup with user confirmation
        
        Args:
            delete_all: If True, delete all except current
            
        Returns:
            Cleanup results dict
        """
        print("\n" + "="*80)
        print("DATABASE CLEANUP")
        print("="*80 + "\n")
        
        # Get storage stats
        stats = self.get_storage_stats()
        
        if stats['total_runs'] == 0:
            print("No database runs found.")
            return {
                'deleted_count': 0,
                'space_freed_bytes': 0,
                'errors': [],
                'deleted_runs': []
            }
        
        # Display current runs
        print(f"📊 Total Runs: {stats['total_runs']}")
        print(f"💾 Total Size: {stats['total_size_human']}")
        print(f"🔄 Current Run: {stats['current_run']}\n")
        
        print("Runs:")
        print("-" * 80)
        
        for run in stats['runs']:
            current_marker = " ⭐ CURRENT" if run['is_current'] else ""
            age_str = f"{run['age_days']:.1f} days ago"
            print(f"  {run['run_id']} | {run['size_human']:>10} | {age_str:>15}{current_marker}")
        
        print("-" * 80 + "\n")
        
        # Determine what will be deleted
        if delete_all:
            print("⚠️  DELETE ALL mode: Will delete all runs except current\n")
        else:
            print(f"Retention Policy: {self.retention_mode}")
            print(f"  - Keep runs from last {self.retention_days} days")
            print(f"  - Keep last {self.retention_count} runs")
            print()
        
        # Dry run to show what will be deleted
        result = self.cleanup_old_runs(dry_run=True)
        
        if result['deleted_count'] == 0:
            print("✅ No runs to delete based on current retention policy.")
            return result
        
        print(f"Will delete {result['deleted_count']} run(s):")
        for run_id in result['deleted_runs']:
            print(f"  - {run_id}")
        print(f"\nSpace to be freed: {result['space_freed_human']}\n")
        
        # Confirm deletion
        try:
            response = input("Proceed with deletion? (y/n): ").strip().lower()
            if response not in ['y', 'yes']:
                print("\n❌ Cleanup cancelled\n")
                return {
                    'deleted_count': 0,
                    'space_freed_bytes': 0,
                    'errors': [],
                    'deleted_runs': []
                }
        except (KeyboardInterrupt, EOFError):
            print("\n\n❌ Cleanup cancelled\n")
            return {
                'deleted_count': 0,
                'space_freed_bytes': 0,
                'errors': [],
                'deleted_runs': []
            }
        
        # Perform actual cleanup
        print("\n🧹 Cleaning up...\n")
        result = self.cleanup_old_runs(dry_run=False)
        
        print(f"\n✅ Cleanup complete!")
        print(f"   Deleted: {result['deleted_count']} run(s)")
        print(f"   Space freed: {result['space_freed_human']}")
        
        if result['errors']:
            print(f"\n⚠️  Errors encountered: {len(result['errors'])}")
            for error in result['errors']:
                print(f"   - {error['run_id']}: {error['error']}")
        
        print("\n" + "="*80 + "\n")
        
        return result
