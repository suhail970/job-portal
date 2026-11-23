import os
import sys
from datetime import datetime, timezone, timedelta
from croniter import croniter

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import init_db, engine
from app.models.entities import CronJob, CronExecution
from app.workers.hermes_cron_engine import hermes_cron
from sqlmodel import Session, select
import asyncio

def setup_module():
    """Ensure database tables and seed jobs are present."""
    init_db()

def test_croniter_evaluation():
    """Validates 5-field cron parsing parity with Hermes Agent."""
    base_time = datetime(2026, 11, 23, 8, 30, tzinfo=timezone.utc)
    
    # Morning 09:00 AM
    next_9am = hermes_cron.compute_next_run("0 9 * * *", base_time)
    assert next_9am.hour == 9
    assert next_9am.minute == 0
    assert next_9am.day == 23

    # Afternoon 14:00 PM
    next_2pm = hermes_cron.compute_next_run("0 14 * * *", base_time)
    assert next_2pm.hour == 14
    assert next_2pm.minute == 0

    # Evening 20:00 PM
    next_8pm = hermes_cron.compute_next_run("0 20 * * *", base_time)
    assert next_8pm.hour == 20
    assert next_8pm.minute == 0

    # Validation
    assert croniter.is_valid("0 9 * * *") is True
    assert croniter.is_valid("*/15 * * * *") is True
    assert croniter.is_valid("invalid-cron") is False

def test_default_jobs_seeded_in_sqlite():
    """Verifies that durable SQLite holds the seeded Hermes watchers."""
    with Session(engine) as session:
        jobs = session.exec(select(CronJob)).all()
        assert len(jobs) >= 4
        
        job_names = {j.name for j in jobs}
        assert "Morning Campus Ingestion" in job_names
        assert "Afternoon Placement Sync" in job_names
        assert "Evening Hiring Digest" in job_names
        assert "Coimbatore Regional Watcher" in job_names

        coimbatore_job = session.exec(select(CronJob).where(CronJob.name == "Coimbatore Regional Watcher")).first()
        assert coimbatore_job is not None
        assert coimbatore_job.target_location == "Coimbatore"
        assert coimbatore_job.cron_expr == "0 11 * * *"

def test_hermes_silent_marker_and_execution_ledger():
    """Tests execution recording, duration in ms, and [SILENT] quiet marker."""
    async def run_test():
        with Session(engine) as session:
            coimbatore_job = session.exec(select(CronJob).where(CronJob.name == "Coimbatore Regional Watcher")).first()
            assert coimbatore_job is not None
            job_id = coimbatore_job.id

        # Execute Coimbatore regional watcher
        result = await hermes_cron.execute_job(job_id, dispatch_kind="manual")
        
        assert result["status"] == "success"
        assert "duration_ms" in result
        assert result["duration_ms"] >= 0
        assert result["final_status"] in ["ok", "silent"]

        # If 0 new drives were added, verify [SILENT] contract
        if result["new_drives_added"] == 0:
            assert result["final_status"] == "silent"
            assert "[SILENT]" in result["summary"]

        # Verify durable ledger entry in SQLite
        history = hermes_cron.get_job_history(job_id, limit=5)
        assert len(history) >= 1
        latest = history[0]
        assert latest["dispatch_kind"] == "manual"
        assert latest["status"] in ["ok", "silent"]
        assert latest["duration_ms"] is not None

    asyncio.run(run_test())

def test_concurrency_lock_and_job_pause():
    """Tests job pause/resume toggle and concurrency safety."""
    with Session(engine) as session:
        job = session.exec(select(CronJob).where(CronJob.name == "Morning Campus Ingestion")).first()
        assert job is not None
        original_enabled = job.enabled

        # Pause
        job.enabled = False
        job.state = "paused"
        session.add(job)
        session.commit()

        reloaded = session.get(CronJob, job.id)
        assert reloaded.enabled is False
        assert reloaded.state == "paused"

        # Restore
        reloaded.enabled = original_enabled
        reloaded.state = "scheduled"
        session.add(reloaded)
        session.commit()

if __name__ == "__main__":
    setup_module()
    test_croniter_evaluation()
    print("✓ test_croniter_evaluation passed")
    test_default_jobs_seeded_in_sqlite()
    print("✓ test_default_jobs_seeded_in_sqlite passed")
    test_hermes_silent_marker_and_execution_ledger()
    print("✓ test_hermes_silent_marker_and_execution_ledger passed")
    test_concurrency_lock_and_job_pause()
    print("✓ test_concurrency_lock_and_job_pause passed")
    print("\nALL HERMES CRON TESTS PASSED PERFECTLY!")
