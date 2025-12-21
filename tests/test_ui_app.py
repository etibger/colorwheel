"""
Smoke test for ConverterApp: ensure clicking Run does not error.
"""
import asyncio
from ui import ConverterApp

def test_ui_click_run_no_error():
    """Start the app headless, click the Run button, and ensure no exceptions."""
    async def run_smoke():
        async with ConverterApp().run_test() as pilot:
            # Allow UI to initialize
            await pilot.pause(0.1)
            # Click the Run button (with default selections)
            await pilot.click("#run")
            # Allow any handlers to execute
            await pilot.pause(0.1)

    # Should complete without raising
    asyncio.run(run_smoke())
