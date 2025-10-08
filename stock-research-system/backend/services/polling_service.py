"""
Advanced Polling Service with WebSocket and Long-Polling Support
Implements real-time updates, progress tracking, and cancellation
"""

import asyncio
import logging
import uuid
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import json
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status states"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PARTIAL = "partial"


class UpdateType(Enum):
    """Types of updates sent to clients"""
    PROGRESS = "progress"
    STATUS = "status"
    RESULT = "result"
    ERROR = "error"
    LOG = "log"
    METRIC = "metric"


@dataclass
class Job:
    """Represents a long-running job"""
    job_id: str
    user_id: str
    task_type: str
    payload: Dict[str, Any]
    status: JobStatus = JobStatus.QUEUED
    progress: float = 0.0
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updates: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    cancel_requested: bool = False


@dataclass
class ProgressUpdate:
    """Progress update for a job"""
    job_id: str
    progress: float
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class PollingService:
    """
    Main polling service with WebSocket and long-polling support
    """

    def __init__(self,
                 websocket_manager=None,
                 job_timeout: int = 300,
                 cleanup_interval: int = 3600):

        # Job storage
        self.jobs: Dict[str, Job] = {}
        self.user_jobs: Dict[str, Set[str]] = defaultdict(set)

        # WebSocket manager for real-time updates
        self.websocket_manager = websocket_manager

        # Long-polling support
        self.pending_updates: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.update_events: Dict[str, asyncio.Event] = {}

        # Configuration
        self.job_timeout = job_timeout
        self.cleanup_interval = cleanup_interval

        # Metrics
        self.metrics = {
            'total_jobs': 0,
            'active_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'cancelled_jobs': 0,
            'average_completion_time': 0
        }

        # Start cleanup task
        asyncio.create_task(self._cleanup_task())

    async def create_job(self,
                        user_id: str,
                        task_type: str,
                        payload: Dict[str, Any],
                        metadata: Dict[str, Any] = None) -> str:
        """
        Create a new job

        Args:
            user_id: User identifier
            task_type: Type of task to execute
            payload: Task payload
            metadata: Optional job metadata

        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())

        job = Job(
            job_id=job_id,
            user_id=user_id,
            task_type=task_type,
            payload=payload,
            metadata=metadata or {}
        )

        self.jobs[job_id] = job
        self.user_jobs[user_id].add(job_id)
        self.metrics['total_jobs'] += 1

        # Create update event for long-polling
        self.update_events[job_id] = asyncio.Event()

        # Send initial status update
        await self._send_update(job_id, UpdateType.STATUS, {
            'status': JobStatus.QUEUED.value,
            'message': 'Job queued for processing'
        })

        logger.info(f"Created job {job_id} for user {user_id}")
        return job_id

    async def start_job(self, job_id: str) -> bool:
        """
        Mark job as started

        Args:
            job_id: Job identifier

        Returns:
            Success status
        """
        job = self.jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False

        if job.cancel_requested:
            await self.cancel_job(job_id)
            return False

        job.status = JobStatus.PROCESSING
        job.started_at = datetime.utcnow()
        self.metrics['active_jobs'] += 1

        await self._send_update(job_id, UpdateType.STATUS, {
            'status': JobStatus.PROCESSING.value,
            'message': 'Job processing started'
        })

        return True

    async def update_progress(self,
                             job_id: str,
                             progress: float,
                             message: str,
                             details: Dict[str, Any] = None) -> bool:
        """
        Update job progress

        Args:
            job_id: Job identifier
            progress: Progress percentage (0-100)
            message: Progress message
            details: Optional progress details

        Returns:
            Success status
        """
        job = self.jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False

        # Check for cancellation
        if job.cancel_requested:
            await self.cancel_job(job_id)
            return False

        job.progress = min(100.0, max(0.0, progress))

        update = ProgressUpdate(
            job_id=job_id,
            progress=job.progress,
            message=message,
            details=details
        )

        job.updates.append({
            'type': UpdateType.PROGRESS.value,
            'data': {
                'progress': update.progress,
                'message': update.message,
                'details': update.details,
                'timestamp': update.timestamp.isoformat()
            }
        })

        await self._send_update(job_id, UpdateType.PROGRESS, {
            'progress': update.progress,
            'message': update.message,
            'details': update.details
        })

        return True

    async def complete_job(self,
                          job_id: str,
                          result: Any,
                          partial: bool = False) -> bool:
        """
        Mark job as completed

        Args:
            job_id: Job identifier
            result: Job result
            partial: Whether this is a partial result

        Returns:
            Success status
        """
        job = self.jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False

        job.status = JobStatus.PARTIAL if partial else JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.result = result
        job.progress = 100.0 if not partial else job.progress

        # Update metrics
        if not partial:
            self.metrics['active_jobs'] = max(0, self.metrics['active_jobs'] - 1)
            self.metrics['completed_jobs'] += 1

            if job.started_at:
                completion_time = (job.completed_at - job.started_at).total_seconds()
                self._update_average_completion_time(completion_time)

        await self._send_update(job_id, UpdateType.RESULT, {
            'status': job.status.value,
            'result': result,
            'partial': partial
        })

        logger.info(f"Job {job_id} completed {'partially' if partial else 'fully'}")
        return True

    async def fail_job(self, job_id: str, error: str) -> bool:
        """
        Mark job as failed

        Args:
            job_id: Job identifier
            error: Error message

        Returns:
            Success status
        """
        job = self.jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False

        job.status = JobStatus.FAILED
        job.completed_at = datetime.utcnow()
        job.error = error

        self.metrics['active_jobs'] = max(0, self.metrics['active_jobs'] - 1)
        self.metrics['failed_jobs'] += 1

        await self._send_update(job_id, UpdateType.ERROR, {
            'status': JobStatus.FAILED.value,
            'error': error
        })

        logger.error(f"Job {job_id} failed: {error}")
        return True

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job

        Args:
            job_id: Job identifier

        Returns:
            Success status
        """
        job = self.jobs.get(job_id)
        if not job:
            logger.error(f"Job {job_id} not found")
            return False

        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return False

        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.utcnow()
        job.cancel_requested = True

        if job.status == JobStatus.PROCESSING:
            self.metrics['active_jobs'] = max(0, self.metrics['active_jobs'] - 1)
        self.metrics['cancelled_jobs'] += 1

        await self._send_update(job_id, UpdateType.STATUS, {
            'status': JobStatus.CANCELLED.value,
            'message': 'Job cancelled'
        })

        logger.info(f"Job {job_id} cancelled")
        return True

    async def request_cancellation(self, job_id: str) -> bool:
        """
        Request job cancellation (for cooperative cancellation)

        Args:
            job_id: Job identifier

        Returns:
            Success status
        """
        job = self.jobs.get(job_id)
        if not job:
            return False

        job.cancel_requested = True
        logger.info(f"Cancellation requested for job {job_id}")
        return True

    def is_cancelled(self, job_id: str) -> bool:
        """
        Check if job cancellation was requested

        Args:
            job_id: Job identifier

        Returns:
            True if cancellation requested
        """
        job = self.jobs.get(job_id)
        return job.cancel_requested if job else False

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status

        Args:
            job_id: Job identifier

        Returns:
            Job status dictionary
        """
        job = self.jobs.get(job_id)
        if not job:
            return None

        return {
            'job_id': job.job_id,
            'status': job.status.value,
            'progress': job.progress,
            'created_at': job.created_at.isoformat(),
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'completed_at': job.completed_at.isoformat() if job.completed_at else None,
            'result': job.result,
            'error': job.error,
            'metadata': job.metadata
        }

    async def get_user_jobs(self, user_id: str, active_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get all jobs for a user

        Args:
            user_id: User identifier
            active_only: Only return active jobs

        Returns:
            List of job status dictionaries
        """
        job_ids = self.user_jobs.get(user_id, set())
        jobs = []

        for job_id in job_ids:
            job = self.jobs.get(job_id)
            if job:
                if active_only and job.status not in [JobStatus.QUEUED, JobStatus.PROCESSING]:
                    continue

                jobs.append(await self.get_job_status(job_id))

        return jobs

    async def long_poll(self,
                       job_id: str,
                       last_update_index: int = 0,
                       timeout: int = 30) -> Dict[str, Any]:
        """
        Long-polling endpoint for clients without WebSocket support

        Args:
            job_id: Job identifier
            last_update_index: Index of last received update
            timeout: Long-poll timeout in seconds

        Returns:
            Updates since last_update_index
        """
        job = self.jobs.get(job_id)
        if not job:
            return {'error': 'Job not found'}

        # Get new updates
        updates = job.updates[last_update_index:]

        if updates:
            # Return immediately if there are new updates
            return {
                'updates': updates,
                'last_index': len(job.updates),
                'status': job.status.value,
                'progress': job.progress
            }

        # Wait for new updates
        try:
            await asyncio.wait_for(
                self.update_events[job_id].wait(),
                timeout=timeout
            )

            # Clear event for next wait
            self.update_events[job_id].clear()

            # Return new updates
            updates = job.updates[last_update_index:]
            return {
                'updates': updates,
                'last_index': len(job.updates),
                'status': job.status.value,
                'progress': job.progress
            }

        except asyncio.TimeoutError:
            # Return empty update on timeout
            return {
                'updates': [],
                'last_index': last_update_index,
                'status': job.status.value,
                'progress': job.progress
            }

    async def _send_update(self, job_id: str, update_type: UpdateType, data: Dict[str, Any]):
        """
        Send update to clients via WebSocket and prepare for long-polling

        Args:
            job_id: Job identifier
            update_type: Type of update
            data: Update data
        """
        job = self.jobs.get(job_id)
        if not job:
            return

        update = {
            'job_id': job_id,
            'type': update_type.value,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }

        # Send via WebSocket if available
        if self.websocket_manager:
            await self.websocket_manager.send_message(
                message=update,
                client_id=job.user_id
            )

        # Store for long-polling
        self.pending_updates[job_id].append(update)

        # Signal update event for long-polling
        if job_id in self.update_events:
            self.update_events[job_id].set()

    async def _cleanup_task(self):
        """
        Periodic cleanup of old jobs
        """
        while True:
            await asyncio.sleep(self.cleanup_interval)

            try:
                cutoff_time = datetime.utcnow() - timedelta(seconds=self.cleanup_interval)
                jobs_to_remove = []

                for job_id, job in self.jobs.items():
                    # Remove completed/failed/cancelled jobs older than cutoff
                    if job.completed_at and job.completed_at < cutoff_time:
                        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                            jobs_to_remove.append(job_id)

                    # Timeout stuck jobs
                    elif job.started_at:
                        elapsed = (datetime.utcnow() - job.started_at).total_seconds()
                        if elapsed > self.job_timeout and job.status == JobStatus.PROCESSING:
                            await self.fail_job(job_id, "Job timeout")
                            jobs_to_remove.append(job_id)

                # Remove old jobs
                for job_id in jobs_to_remove:
                    job = self.jobs.pop(job_id, None)
                    if job:
                        self.user_jobs[job.user_id].discard(job_id)
                        self.pending_updates.pop(job_id, None)
                        self.update_events.pop(job_id, None)

                logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    def _update_average_completion_time(self, completion_time: float):
        """Update rolling average completion time"""
        n = self.metrics['completed_jobs']
        if n == 1:
            self.metrics['average_completion_time'] = completion_time
        else:
            avg = self.metrics['average_completion_time']
            self.metrics['average_completion_time'] = (avg * (n - 1) + completion_time) / n

    def get_metrics(self) -> Dict[str, Any]:
        """Get service metrics"""
        return {
            **self.metrics,
            'timestamp': datetime.utcnow().isoformat()
        }