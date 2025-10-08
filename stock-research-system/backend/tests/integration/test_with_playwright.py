"""
Playwright End-to-End Tests for Stock Research System
Tests the full UI and backend integration
"""

import asyncio
import json
from playwright.async_api import async_playwright
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)


class StockResearchE2ETest:
    """End-to-end tests using Playwright"""

    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.api_url = "http://localhost:8000"
        self.browser = None
        self.page = None

    async def setup(self):
        """Setup browser and page"""
        logger.info("Setting up Playwright browser...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Set to True for CI/CD
            slow_mo=500  # Slow down actions for visibility
        )
        context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await context.new_page()

        # Enable console logging
        self.page.on("console", lambda msg: logger.info(f"Browser console: {msg.text}"))

        logger.info("✓ Browser setup complete")

    async def teardown(self):
        """Cleanup browser"""
        if self.browser:
            await self.browser.close()
            logger.info("✓ Browser closed")

    async def test_homepage_load(self):
        """Test that homepage loads correctly"""
        logger.info("=== Testing Homepage Load ===")

        await self.page.goto(self.base_url)
        await self.page.wait_for_load_state("networkidle")

        # Check for main elements
        title = await self.page.title()
        logger.info(f"Page title: {title}")

        # Check for chat interface
        chat_input = await self.page.query_selector('input[placeholder*="investment"], textarea[placeholder*="investment"]')
        assert chat_input is not None, "Chat input not found"

        logger.info("✓ Homepage loaded successfully")

        # Take screenshot
        await self.page.screenshot(path="screenshots/homepage.png")

    async def test_chat_interaction(self):
        """Test chat functionality with AI"""
        logger.info("=== Testing Chat Interaction ===")

        await self.page.goto(self.base_url)
        await self.page.wait_for_load_state("networkidle")

        # Find and interact with chat
        chat_input = await self.page.wait_for_selector(
            'input[placeholder*="investment"], textarea[placeholder*="Type"], input[type="text"]',
            timeout=10000
        )

        # Send a simple query
        test_query = "What is the current price of AAPL?"
        await chat_input.fill(test_query)
        logger.info(f"Entered query: {test_query}")

        # Submit (try multiple methods)
        await self.page.keyboard.press("Enter")

        # Wait for response
        await self.page.wait_for_timeout(3000)

        # Check for response elements
        response_elements = await self.page.query_selector_all('.MuiCard-root, .MuiPaper-root')
        logger.info(f"Found {len(response_elements)} response elements")

        # Take screenshot
        await self.page.screenshot(path="screenshots/chat_response.png")

        logger.info("✓ Chat interaction test completed")

    async def test_stock_analysis_flow(self):
        """Test complete stock analysis workflow"""
        logger.info("=== Testing Stock Analysis Flow ===")

        await self.page.goto(self.base_url)
        await self.page.wait_for_load_state("networkidle")

        # Enter analysis query
        chat_input = await self.page.wait_for_selector(
            'input[placeholder*="investment"], textarea[placeholder*="Type"], input[type="text"]',
            timeout=10000
        )

        analysis_query = "Analyze AAPL and NVDA for investment. Should I buy?"
        await chat_input.fill(analysis_query)
        logger.info(f"Entered analysis query: {analysis_query}")

        # Submit
        await self.page.keyboard.press("Enter")

        # Wait for analysis to start (look for progress indicators)
        await self.page.wait_for_timeout(2000)

        # Check for progress indicators
        progress_indicators = await self.page.query_selector_all('.MuiLinearProgress-root, .MuiCircularProgress-root')
        if progress_indicators:
            logger.info(f"✓ Found {len(progress_indicators)} progress indicators")

        # Wait for some results
        await self.page.wait_for_timeout(5000)

        # Take screenshot of analysis in progress
        await self.page.screenshot(path="screenshots/analysis_progress.png")

        logger.info("✓ Stock analysis flow initiated")

    async def test_agent_visualization(self):
        """Test agent visualization dashboard"""
        logger.info("=== Testing Agent Visualization ===")

        # First trigger an analysis to have active agents
        await self.test_stock_analysis_flow()

        # Look for agent visualization components
        agent_cards = await self.page.query_selector_all('[class*="agent"], [class*="Agent"]')
        logger.info(f"Found {len(agent_cards)} agent-related elements")

        # Check for ReactFlow canvas (if visible)
        flow_canvas = await self.page.query_selector('.react-flow, [class*="reactflow"]')
        if flow_canvas:
            logger.info("✓ Found agent flow visualization")
            await self.page.screenshot(path="screenshots/agent_flow.png")

        # Check for real-time events
        event_stream = await self.page.query_selector('[class*="event"], [class*="Event"]')
        if event_stream:
            logger.info("✓ Found event stream component")

    async def test_memory_visualization(self):
        """Test memory system visualization"""
        logger.info("=== Testing Memory Visualization ===")

        # Look for memory-related components
        memory_tabs = await self.page.query_selector_all('[role="tab"]')

        for tab in memory_tabs:
            tab_text = await tab.text_content()
            if "memory" in tab_text.lower():
                logger.info(f"Found memory tab: {tab_text}")
                await tab.click()
                await self.page.wait_for_timeout(1000)
                await self.page.screenshot(path=f"screenshots/memory_{tab_text.replace(' ', '_')}.png")

        # Check for pattern detection
        patterns = await self.page.query_selector_all('[class*="pattern"], [class*="Pattern"]')
        if patterns:
            logger.info(f"✓ Found {len(patterns)} pattern elements")

        # Check for insights
        insights = await self.page.query_selector_all('[class*="insight"], [class*="Insight"]')
        if insights:
            logger.info(f"✓ Found {len(insights)} insight elements")

    async def test_websocket_connection(self):
        """Test WebSocket real-time updates"""
        logger.info("=== Testing WebSocket Connection ===")

        # Monitor WebSocket connections
        ws_connected = False

        def handle_websocket(ws):
            nonlocal ws_connected
            ws_connected = True
            logger.info(f"WebSocket connected: {ws.url}")

        self.page.on("websocket", handle_websocket)

        # Navigate and trigger WebSocket connection
        await self.page.goto(self.base_url)
        await self.page.wait_for_timeout(3000)

        if ws_connected:
            logger.info("✓ WebSocket connection established")
        else:
            logger.warning("⚠ No WebSocket connection detected")

    async def test_api_endpoints(self):
        """Test backend API endpoints directly"""
        logger.info("=== Testing API Endpoints ===")

        # Test health endpoint
        response = await self.page.request.get(f"{self.api_url}/health")
        assert response.status == 200
        health_data = await response.json()
        logger.info(f"Health check: {health_data}")

        # Test chat endpoint
        chat_response = await self.page.request.post(
            f"{self.api_url}/api/v1/chat",
            data={
                "message": "Hello, can you help me with stock analysis?",
                "user_id": "test_user"
            }
        )
        assert chat_response.status == 200
        chat_data = await chat_response.json()
        logger.info(f"Chat response received: {chat_data.get('response', '')[:100]}...")

        # Test market data endpoint
        market_response = await self.page.request.get(f"{self.api_url}/api/v1/market/price/AAPL")
        if market_response.status == 200:
            market_data = await market_response.json()
            logger.info(f"AAPL price data: {market_data}")

        logger.info("✓ API endpoints tested")

    async def test_responsive_design(self):
        """Test responsive design on different viewports"""
        logger.info("=== Testing Responsive Design ===")

        viewports = [
            {"name": "Mobile", "width": 375, "height": 667},
            {"name": "Tablet", "width": 768, "height": 1024},
            {"name": "Desktop", "width": 1920, "height": 1080}
        ]

        for viewport in viewports:
            await self.page.set_viewport_size(
                width=viewport["width"],
                height=viewport["height"]
            )
            await self.page.goto(self.base_url)
            await self.page.wait_for_load_state("networkidle")
            await self.page.screenshot(
                path=f"screenshots/responsive_{viewport['name'].lower()}.png"
            )
            logger.info(f"✓ Tested {viewport['name']} viewport")

    async def test_error_handling(self):
        """Test error handling and recovery"""
        logger.info("=== Testing Error Handling ===")

        # Test with invalid input
        await self.page.goto(self.base_url)
        await self.page.wait_for_load_state("networkidle")

        chat_input = await self.page.wait_for_selector(
            'input[placeholder*="investment"], textarea[placeholder*="Type"], input[type="text"]',
            timeout=10000
        )

        # Send empty query
        await chat_input.fill("")
        await self.page.keyboard.press("Enter")
        await self.page.wait_for_timeout(1000)

        # Check for error message
        error_elements = await self.page.query_selector_all('[class*="error"], [class*="Error"], [role="alert"]')
        if error_elements:
            logger.info(f"✓ Found {len(error_elements)} error handling elements")

        # Test with very long input
        long_input = "AAPL " * 100
        await chat_input.fill(long_input)
        await self.page.keyboard.press("Enter")
        await self.page.wait_for_timeout(1000)

        logger.info("✓ Error handling tested")

    async def run_all_tests(self):
        """Run all E2E tests"""
        logger.info("Starting E2E tests for Stock Research System...")
        logger.info("="*50)

        try:
            await self.setup()

            # Run tests in sequence
            await self.test_homepage_load()
            await self.test_websocket_connection()
            await self.test_chat_interaction()
            await self.test_stock_analysis_flow()
            await self.test_agent_visualization()
            await self.test_memory_visualization()
            await self.test_api_endpoints()
            await self.test_responsive_design()
            await self.test_error_handling()

            logger.info("\n" + "="*50)
            logger.info("✅ ALL E2E TESTS COMPLETED SUCCESSFULLY!")
            logger.info("="*50)
            logger.info("\nScreenshots saved in ./screenshots/")

        except Exception as e:
            logger.error(f"\n❌ TEST FAILED: {e}")
            # Take error screenshot
            if self.page:
                await self.page.screenshot(path="screenshots/error.png")
            raise
        finally:
            await self.teardown()


async def main():
    """Main test runner"""
    import os

    # Create screenshots directory
    os.makedirs("screenshots", exist_ok=True)

    # Run tests
    tester = StockResearchE2ETest()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())