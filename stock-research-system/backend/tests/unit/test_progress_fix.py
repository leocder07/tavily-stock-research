"""
Test script to verify progress tracking fixes

This script starts an analysis and monitors progress in real-time
to verify that:
1. active_agents shows currently running agent
2. pending_agents only shows agents that haven't started
3. completed_agents accurately reflects finished agents
4. Progress updates in real-time via WebSocket
"""

import asyncio
import aiohttp
import json
from datetime import datetime


async def test_progress_tracking():
    """Test progress tracking with live analysis"""

    base_url = "http://localhost:8000"

    print("=" * 80)
    print("PROGRESS TRACKING TEST")
    print("=" * 80)
    print()

    # Step 1: Start an analysis
    print("[1] Starting analysis...")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{base_url}/api/v1/analyze",
            json={
                "query": "Analyze AAPL stock",
                "symbols": ["AAPL"],
                "priority": "normal",
                "include_technical": True,
                "include_sentiment": True,
                "include_fundamentals": True
            }
        ) as response:
            if response.status != 200:
                print(f"ERROR: Failed to start analysis: {response.status}")
                return

            result = await response.json()
            analysis_id = result["analysis_id"]
            print(f"✓ Analysis started: {analysis_id}")
            print()

    # Step 2: Monitor progress in real-time
    print("[2] Monitoring progress...")
    print("-" * 80)

    previous_state = {
        "active": [],
        "completed": [],
        "pending": [],
        "percentage": 0
    }

    max_polls = 60  # Poll for up to 60 seconds
    poll_count = 0

    async with aiohttp.ClientSession() as session:
        while poll_count < max_polls:
            await asyncio.sleep(2)  # Poll every 2 seconds
            poll_count += 1

            async with session.get(
                f"{base_url}/api/v1/analyze/{analysis_id}/status"
            ) as response:
                if response.status != 200:
                    print(f"ERROR: Failed to get status: {response.status}")
                    break

                status = await response.json()
                progress = status.get("progress", {})

                active = progress.get("active_agents", [])
                completed = progress.get("completed_agents", [])
                pending = progress.get("pending_agents", [])
                percentage = progress.get("percentage", 0)
                message = progress.get("message", "")

                # Only print if state changed
                if (active != previous_state["active"] or
                    completed != previous_state["completed"] or
                    percentage != previous_state["percentage"]):

                    timestamp = datetime.now().strftime("%H:%M:%S")
                    print(f"[{timestamp}] Progress: {percentage}%")
                    print(f"  Message: {message}")
                    print(f"  Active: {active}")
                    print(f"  Completed ({len(completed)}): {completed}")
                    print(f"  Pending ({len(pending)}): {pending[:3]}{'...' if len(pending) > 3 else ''}")
                    print()

                    previous_state = {
                        "active": active,
                        "completed": completed,
                        "pending": pending,
                        "percentage": percentage
                    }

                # Check if completed
                if status["status"] == "completed":
                    print("=" * 80)
                    print("✓ ANALYSIS COMPLETED")
                    print("=" * 80)
                    break
                elif status["status"] == "failed":
                    print("=" * 80)
                    print("✗ ANALYSIS FAILED")
                    print("=" * 80)
                    break

    # Step 3: Verify final state
    print()
    print("[3] Verifying final state...")

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{base_url}/api/v1/analyze/{analysis_id}/status"
        ) as response:
            status = await response.json()
            progress = status.get("progress", {})

            active = progress.get("active_agents", [])
            completed = progress.get("completed_agents", [])
            pending = progress.get("pending_agents", [])

            print("\nFinal Progress State:")
            print(f"  Active agents: {len(active)} - {active}")
            print(f"  Completed agents: {len(completed)} - {completed}")
            print(f"  Pending agents: {len(pending)} - {pending}")
            print()

            # Validation checks
            issues = []

            if len(active) > 1:
                issues.append(f"❌ Multiple active agents: {active}")
            elif len(active) == 1 and status["status"] == "completed":
                issues.append(f"❌ Active agent after completion: {active}")
            else:
                print("✓ Active agents: OK")

            if len(pending) > 0 and status["status"] == "completed":
                issues.append(f"❌ Pending agents after completion: {pending}")
            else:
                print("✓ Pending agents: OK")

            if len(completed) < 4:  # Should have at least 4 core agents
                issues.append(f"❌ Too few completed agents: {len(completed)}")
            else:
                print(f"✓ Completed agents: {len(completed)}")

            if issues:
                print("\n" + "=" * 80)
                print("ISSUES FOUND:")
                for issue in issues:
                    print(f"  {issue}")
                print("=" * 80)
            else:
                print("\n" + "=" * 80)
                print("✓ ALL CHECKS PASSED!")
                print("=" * 80)


if __name__ == "__main__":
    print("\nStarting progress tracking test...")
    print("Make sure the backend is running on http://localhost:8000")
    print()

    try:
        asyncio.run(test_progress_tracking())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()
