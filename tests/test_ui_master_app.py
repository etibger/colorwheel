"""
UI tests for the master control interface.

Overview
--------
Exercises selection and launch behavior in ``ui_master_app.MasterApp``.
"""

import asyncio
import sys

import pytest

import ui_master_app


def test_build_launch_command_rejects_unknown():
    """Unknown launch keys raise ``ValueError``."""
    with pytest.raises(ValueError):
        ui_master_app.build_launch_command("unknown")


def test_master_ui_launches_data_converter(monkeypatch):
    """Default selection launches the data format conversion UI."""
    captured = {}

    def fake_spawn(command):
        captured["command"] = command
        return None

    monkeypatch.setattr(ui_master_app, "spawn_app", fake_spawn)

    async def run_case():
        async with ui_master_app.MasterApp().run_test() as pilot:
            await pilot.pause(0.1)
            await pilot.click("#launch")
            await pilot.pause(0.1)

    asyncio.run(run_case())

    command = captured.get("command")
    assert command is not None
    assert command[0] == sys.executable
    assert command[-1].endswith("ui_data_fmt_conv.py")


def test_master_ui_launches_palette(monkeypatch):
    """Selecting the palette option launches the palette UI."""
    captured = {}

    def fake_spawn(command):
        captured["command"] = command
        return None

    monkeypatch.setattr(ui_master_app, "spawn_app", fake_spawn)

    async def run_case():
        async with ui_master_app.MasterApp().run_test() as pilot:
            await pilot.pause(0.1)
            await pilot.click("#palette_gen")
            await pilot.click("#launch")
            await pilot.pause(0.1)

    asyncio.run(run_case())

    command = captured.get("command")
    assert command is not None
    assert command[0] == sys.executable
    assert command[-1].endswith("ui_color_palett_app.py")


def test_master_ui_launch_uses_suspend(monkeypatch):
    """Launching from the master UI runs under a suspend context."""
    state = {"active": False, "spawned_with_suspend": False}

    class DummySuspend:
        """Context manager that tracks suspend state."""

        def __enter__(self):
            state["active"] = True

        def __exit__(self, exc_type, exc, exc_tb):
            state["active"] = False

    def fake_suspend(self):
        return DummySuspend()

    def fake_spawn(command):
        state["spawned_with_suspend"] = state["active"]
        return None

    monkeypatch.setattr(ui_master_app.MasterApp, "suspend", fake_suspend)
    monkeypatch.setattr(ui_master_app, "spawn_app", fake_spawn)

    async def run_case():
        async with ui_master_app.MasterApp().run_test() as pilot:
            await pilot.pause(0.1)
            await pilot.click("#launch")
            await pilot.pause(0.1)

    asyncio.run(run_case())

    assert state["spawned_with_suspend"] is True
