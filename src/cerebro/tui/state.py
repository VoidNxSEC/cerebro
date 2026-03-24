"""
TUI State Persistence

Saves and loads TUI state between sessions.
"""

import json
from pathlib import Path
from typing import Any, Optional
from datetime import datetime


class TUIState:
    """
    Manages TUI state persistence.

    Saves user preferences, history, and screen states to ~/.cerebro/tui_state.json
    """

    def __init__(self):
        """Initialize state manager."""
        self.state_dir = Path.home() / ".cerebro"
        self.state_file = self.state_dir / "tui_state.json"
        self.state = self.load()

    def load(self) -> dict[str, Any]:
        """
        Load state from disk.

        Returns:
            dict: Loaded state or default empty state
        """
        # Create directory if it doesn't exist
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Load state if file exists
        if self.state_file.exists():
            try:
                with open(self.state_file, "r") as f:
                    state = json.load(f)
                return state
            except (json.JSONDecodeError, IOError):
                # Return default state if file is corrupted
                return self.default_state()
        else:
            # Create default state
            return self.default_state()

    def default_state(self) -> dict[str, Any]:
        """
        Get default state structure.

        Returns:
            dict: Default empty state
        """
        return {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "last_screen": "dashboard",
            "preferences": {
                "auto_refresh": True,
                "refresh_interval": 10,
                "theme": "default"
            },
            "intelligence": {
                "query_history": [],
                "last_mode": "semantic",
                "last_limit": 10
            },
            "projects": {
                "last_filter": "",
                "sort_column": "name",
                "sort_order": "asc"
            },
            "logs": {
                "last_level_filter": "ALL",
                "last_module_filter": "",
                "paused": False
            },
            "gcp": {
                "last_queries": 100,
                "last_workers": 10
            }
        }

    def save(self) -> None:
        """Save state to disk."""
        try:
            self.state["last_updated"] = datetime.now().isoformat()

            with open(self.state_file, "w") as f:
                json.dump(self.state, f, indent=2)
        except IOError as e:
            # Fail silently - state persistence is not critical
            pass

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a value from state.

        Args:
            key: Dot-separated key path (e.g., "intelligence.query_history")
            default: Default value if key doesn't exist

        Returns:
            Value from state or default
        """
        keys = key.split(".")
        value = self.state

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set a value in state.

        Args:
            key: Dot-separated key path
            value: Value to set
        """
        keys = key.split(".")
        target = self.state

        # Navigate to the target location
        for k in keys[:-1]:
            if k not in target:
                target[k] = {}
            target = target[k]

        # Set the value
        target[keys[-1]] = value

        # Auto-save after setting
        self.save()

    def add_to_history(self, category: str, item: Any, max_items: int = 20) -> None:
        """
        Add an item to a history list.

        Args:
            category: Category name (e.g., "intelligence.query_history")
            item: Item to add
            max_items: Maximum number of items to keep
        """
        history = self.get(category, [])

        if not isinstance(history, list):
            history = []

        # Add new item to beginning
        history.insert(0, item)

        # Trim to max items
        history = history[:max_items]

        # Save back
        self.set(category, history)

    def clear_history(self, category: str) -> None:
        """
        Clear a history category.

        Args:
            category: Category to clear
        """
        self.set(category, [])

    def reset(self) -> None:
        """Reset state to defaults."""
        self.state = self.default_state()
        self.save()
