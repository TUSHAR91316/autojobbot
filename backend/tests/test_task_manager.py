import pytest
import asyncio
from backend.app.services.task_manager import task_manager
from backend.app.models.application import JobApplication, ApplicationStatus
from backend.app.models.job import JobListing


@pytest.mark.asyncio
async def test_task_manager_lifecycle(db_session):
    # Ensure fresh state
    task_manager.stop_session()
    task_manager.is_active = False
    task_manager.status = "IDLE"

    # Start session
    res_start = task_manager.start_session(target=5, delay=1.0)
    assert res_start["success"] is True
    assert task_manager.is_active is True
    assert task_manager.target_count == 5

    # Pause session
    res_pause = task_manager.pause_session()
    assert res_pause["success"] is True
    assert task_manager.is_paused is True
    assert task_manager.status == "PAUSED"

    # Resume session
    res_resume = task_manager.resume_session()
    assert res_resume["success"] is True
    assert task_manager.is_paused is False
    assert task_manager.status == "RUNNING"

    # Stop session
    res_stop = task_manager.stop_session()
    assert res_stop["success"] is True
    assert task_manager._stop_requested is True

    # Cleanup
    task_manager.is_active = False
    task_manager.status = "IDLE"
