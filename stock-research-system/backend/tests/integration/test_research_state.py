#!/usr/bin/env python3
"""Test ResearchDivisionState validation to find the issue"""

from agents.orchestrators.research_leader import ResearchDivisionState, ResearchTask
from datetime import datetime
from services.progress_tracker import Citation

# Test 1: Try creating with all required fields
print("Test 1: Creating ResearchDivisionState with required fields...")
try:
    state = ResearchDivisionState(
        task="Gather market data, news, and sentiment",
        parent_query="NVIDIA stock analysis",
        request_id="test-123",
        priority="high",
        context={"test": "data"},
        research_tasks=None,
        worker_results=[],
        division_summary=None,
        key_insights=None,
        citations=[],
        confidence=0.5
    )
    print("✅ Success! State created with required fields only")
    print(f"   State fields: {state.model_fields_set}")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 2: Try with all fields including optional ones
print("\nTest 2: Creating ResearchDivisionState with all fields...")
try:
    state = ResearchDivisionState(
        task="Gather market data, news, and sentiment",
        parent_query="NVIDIA stock analysis",
        request_id="test-123",
        priority="high",
        context={"test": "data"},
        research_tasks=[],
        worker_results=[],
        division_summary="Test summary",
        key_insights=["insight1", "insight2"],
        citations=[],
        confidence=0.5,
        start_time=datetime.utcnow(),
        completion_time=None
    )
    print("✅ Success! State created with all fields")
except Exception as e:
    print(f"❌ Failed: {e}")

# Test 3: Test the actual data being passed in workflow_adapter
print("\nTest 3: Testing actual workflow_adapter data structure...")
try:
    research_state = {
        "task": "Gather market data, news, and sentiment",
        "parent_query": "NVIDIA stock analysis",
        "request_id": "test-123",
        "priority": "high",
        "context": {"strategic_plan": {}},
        "research_tasks": None,
        "worker_results": [],
        "division_summary": None,
        "key_insights": None,
        "citations": [],
        "confidence": 0.5
    }

    # Try creating from dict
    state = ResearchDivisionState(**research_state)
    print("✅ Success! State created from workflow_adapter dict")
except Exception as e:
    print(f"❌ Failed: {e}")
    print(f"   Required fields: {ResearchDivisionState.model_fields.keys()}")

# Test 4: Check what fields are actually required
print("\nTest 4: Checking required fields...")
for field_name, field_info in ResearchDivisionState.model_fields.items():
    is_required = field_info.is_required()
    default = field_info.default if hasattr(field_info, 'default') else "No default"
    print(f"   {field_name}: required={is_required}, default={default}")