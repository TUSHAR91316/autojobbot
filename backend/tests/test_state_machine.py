import pytest
from backend.app.models.application import JobApplication, ApplicationStatus, VALID_TRANSITIONS


def test_valid_state_transitions():
    # Verify transitions from QUEUED
    assert ApplicationStatus.PREPARING in VALID_TRANSITIONS[ApplicationStatus.QUEUED]
    assert ApplicationStatus.SKIPPED in VALID_TRANSITIONS[ApplicationStatus.QUEUED]
    assert ApplicationStatus.CANCELLED in VALID_TRANSITIONS[ApplicationStatus.QUEUED]

    # Verify transitions from PREPARING
    assert ApplicationStatus.AWAITING_REVIEW in VALID_TRANSITIONS[ApplicationStatus.PREPARING]
    assert ApplicationStatus.READY_TO_SUBMIT in VALID_TRANSITIONS[ApplicationStatus.PREPARING]
    assert ApplicationStatus.MANUAL_ACTION_REQUIRED in VALID_TRANSITIONS[ApplicationStatus.PREPARING]

    # Verify terminal status SUBMITTED has no forward transitions
    assert len(VALID_TRANSITIONS[ApplicationStatus.SUBMITTED]) == 0


def test_state_flow_simulation():
    current_state = ApplicationStatus.QUEUED
    
    # Move to PREPARING
    assert ApplicationStatus.PREPARING in VALID_TRANSITIONS[current_state]
    current_state = ApplicationStatus.PREPARING
    
    # Move to READY_TO_SUBMIT
    assert ApplicationStatus.READY_TO_SUBMIT in VALID_TRANSITIONS[current_state]
    current_state = ApplicationStatus.READY_TO_SUBMIT
    
    # Move to SUBMITTED
    assert ApplicationStatus.SUBMITTED in VALID_TRANSITIONS[current_state]
    current_state = ApplicationStatus.SUBMITTED
    
    assert current_state == ApplicationStatus.SUBMITTED
