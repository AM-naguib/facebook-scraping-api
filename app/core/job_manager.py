"""
Job Manager for handling concurrent scraping tasks
"""
import threading
import time
import uuid
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, asdict

from app.config import settings


class JobStatus(Enum):
    """Job status enumeration"""
    QUEUED = "queued"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobInfo:
    """Job information structure"""
    job_id: str
    job_type: str  # 'reactions' or 'comments'
    status: JobStatus
    post_url: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: Dict[str, Any] = None
    result: Dict[str, Any] = None
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['status'] = self.status.value
        
        # Convert datetime objects to ISO strings
        for field in ['created_at', 'started_at', 'completed_at']:
            if data[field]:
                data[field] = data[field].isoformat()
        
        return data


class JobManager:
    """Manager for handling concurrent scraping jobs"""
    
    def __init__(self):
        """Initialize job manager"""
        self.jobs: Dict[str, JobInfo] = {}
        self.active_threads: Dict[str, threading.Thread] = {}
        self.lock = threading.Lock()
        
        # Create results directory
        os.makedirs(settings.RESULTS_DIR, exist_ok=True)
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_expired_jobs, daemon=True)
        self.cleanup_thread.start()
    
    def create_job(self, job_type: str, post_url: str, **kwargs) -> str:
        """Create a new job and return job ID"""
        job_id = self._generate_job_id(job_type)
        
        job_info = JobInfo(
            job_id=job_id,
            job_type=job_type,
            status=JobStatus.QUEUED,
            post_url=post_url,
            created_at=datetime.now(),
            progress={"percentage": 0, "message": "في قائمة الانتظار"}
        )
        
        with self.lock:
            self.jobs[job_id] = job_info
        
        return job_id
    
    def start_job(self, job_id: str, worker_function: Callable, *args, **kwargs) -> bool:
        """Start a job in a separate thread"""
        with self.lock:
            if job_id not in self.jobs:
                return False
            
            if len(self.active_threads) >= settings.MAX_CONCURRENT_JOBS:
                return False
            
            job = self.jobs[job_id]
            if job.status != JobStatus.QUEUED:
                return False
            
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            job.progress = {"percentage": 0, "message": "بدء المعالجة..."}
            
            # Create and start thread
            thread = threading.Thread(
                target=self._worker_wrapper,
                args=(job_id, worker_function, args, kwargs),
                daemon=True
            )
            
            self.active_threads[job_id] = thread
            thread.start()
            
            return True
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get job status and progress"""
        with self.lock:
            if job_id not in self.jobs:
                return None
            
            job = self.jobs[job_id]
            return job.to_dict()
    
    def get_job_result_file(self, job_id: str) -> Optional[str]:
        """Get the result file path for a completed job"""
        with self.lock:
            if job_id not in self.jobs:
                return None
            
            job = self.jobs[job_id]
            if job.status != JobStatus.COMPLETED or not job.file_path:
                return None
            
            # Check if file exists
            if os.path.exists(job.file_path):
                return job.file_path
            
            return None
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a job (only if queued)"""
        with self.lock:
            if job_id not in self.jobs:
                return False
            
            job = self.jobs[job_id]
            if job.status == JobStatus.QUEUED:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.now()
                return True
            
            return False
    
    def get_active_jobs_count(self) -> int:
        """Get number of currently active jobs"""
        with self.lock:
            return len(self.active_threads)
    
    def get_all_jobs_summary(self) -> Dict:
        """Get summary of all jobs"""
        with self.lock:
            summary = {
                "total_jobs": len(self.jobs),
                "active_jobs": len(self.active_threads),
                "available_slots": settings.MAX_CONCURRENT_JOBS - len(self.active_threads),
                "jobs_by_status": {}
            }
            
            for job in self.jobs.values():
                status = job.status.value
                summary["jobs_by_status"][status] = summary["jobs_by_status"].get(status, 0) + 1
            
            return summary
    
    def _generate_job_id(self, job_type: str) -> str:
        """Generate unique job ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{job_type}_{timestamp}_{unique_id}"
    
    def _worker_wrapper(self, job_id: str, worker_function: Callable, args: tuple, kwargs: dict):
        """Wrapper function for worker threads"""
        try:
            # Update progress
            self._update_job_progress(job_id, 10, "جاري بدء المعالجة...")
            
            # Call the actual worker function
            result = worker_function(job_id, self._update_job_progress, *args, **kwargs)
            
            # Save result to file
            file_path = self._save_result_to_file(job_id, result)
            
            # Update job as completed
            with self.lock:
                if job_id in self.jobs:
                    job = self.jobs[job_id]
                    job.status = JobStatus.COMPLETED
                    job.completed_at = datetime.now()
                    job.result = {
                        "total_items": result.get("total_reactions", result.get("total_comments", 0)),
                        "file_size": self._get_file_size(file_path) if file_path else 0,
                        "download_expires_at": (datetime.now() + timedelta(hours=settings.CLEANUP_AFTER_HOURS)).isoformat()
                    }
                    job.file_path = file_path
                    job.progress = {"percentage": 100, "message": "تم الانتهاء بنجاح"}
        
        except Exception as e:
            # Update job as failed
            with self.lock:
                if job_id in self.jobs:
                    job = self.jobs[job_id]
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.now()
                    job.error_message = str(e)
                    job.progress = {"percentage": 0, "message": f"فشل: {str(e)}"}
        
        finally:
            # Remove from active threads
            with self.lock:
                if job_id in self.active_threads:
                    del self.active_threads[job_id]
    
    def _update_job_progress(self, job_id: str, percentage: int, message: str):
        """Update job progress"""
        with self.lock:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                if job.progress is None:
                    job.progress = {}
                job.progress.update({
                    "percentage": percentage,
                    "message": message,
                    "updated_at": datetime.now().isoformat()
                })
    
    def _save_result_to_file(self, job_id: str, result: Dict) -> Optional[str]:
        """Save job result to file"""
        try:
            if not result or result.get("error"):
                return None
            
            file_name = f"{job_id}.json"
            file_path = os.path.join(settings.RESULTS_DIR, file_name)
            
            # Add metadata
            output_data = {
                "job_info": {
                    "job_id": job_id,
                    "scraped_at": datetime.now().isoformat(),
                    "api_version": settings.API_VERSION
                },
                **result
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            return file_path
            
        except Exception as e:
            print(f"❌ خطأ في حفظ النتائج: {e}")
            return None
    
    def _get_file_size(self, file_path: str) -> str:
        """Get human readable file size"""
        try:
            size_bytes = os.path.getsize(file_path)
            
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
        except:
            return "Unknown"
    
    def _cleanup_expired_jobs(self):
        """Background thread to cleanup expired jobs and files"""
        while True:
            try:
                cutoff_time = datetime.now() - timedelta(hours=settings.CLEANUP_AFTER_HOURS)
                
                with self.lock:
                    expired_jobs = []
                    
                    for job_id, job in self.jobs.items():
                        if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] 
                            and job.completed_at and job.completed_at < cutoff_time):
                            expired_jobs.append(job_id)
                    
                    # Remove expired jobs and their files
                    for job_id in expired_jobs:
                        job = self.jobs[job_id]
                        
                        # Delete file if exists
                        if job.file_path and os.path.exists(job.file_path):
                            try:
                                os.remove(job.file_path)
                            except:
                                pass
                        
                        # Remove from jobs dict
                        del self.jobs[job_id]
                
                # Sleep for 1 hour before next cleanup
                time.sleep(3600)
                
            except Exception as e:
                print(f"❌ خطأ في تنظيف المهام المنتهية الصلاحية: {e}")
                time.sleep(3600)


# Global job manager instance
job_manager = JobManager()


