"""
Real-Time Repository Watcher

Polls all tracked git repos for HEAD changes.  When a change is detected,
re-collects metrics for that repo and fires an async callback (used by the
FastAPI server to push updates over WebSocket).

Design: HEAD-hash polling only — no inotify / watchdog dependency.
"""

import asyncio
import logging
import os
from collections.abc import Callable, Coroutine
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cerebro.core.metrics_collector import MetricsCollector

logger = logging.getLogger("cerebro.watcher")


class RepoWatcher:
    def __init__(
        self,
        arch_path: str = os.getenv("CEREBRO_ARCH_PATH", str(Path.home() / "master")),
        poll_interval: int = 10,
        on_change: Callable[[dict[str, Any]], Coroutine] | None = None,
    ):
        self.collector = MetricsCollector(arch_path)
        self.poll_interval = poll_interval
        self.on_change = on_change

        self._head_cache: dict[str, str] = {}
        self._tracked_repos: list[Path] = []
        self._running = False
        self._task: asyncio.Task | None = None
        self._poll_count = 0

        self.last_update: str | None = None
        self.changes_detected: int = 0

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._tracked_repos = self.collector.discover_repos()
        for repo in self._tracked_repos:
            self._head_cache[repo.name] = self.collector.get_head_hash(repo)
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Watcher started — tracking %d repos (interval %ds)", len(self._tracked_repos), self.poll_interval)

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Watcher stopped")

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def tracked_count(self) -> int:
        return len(self._tracked_repos)

    def refresh_repo_list(self) -> None:
        self._tracked_repos = self.collector.discover_repos()
        for repo in self._tracked_repos:
            if repo.name not in self._head_cache:
                self._head_cache[repo.name] = self.collector.get_head_hash(repo)

    # ------------------------------------------------------------------
    # Polling loop
    # ------------------------------------------------------------------
    async def _poll_loop(self) -> None:
        while self._running:
            self._poll_count += 1
            # refresh repo list every ~60 s
            if self._poll_count % max(1, 60 // self.poll_interval) == 0:
                self.refresh_repo_list()
            try:
                await self._check_all()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Watcher poll error: %s", e)
            await asyncio.sleep(self.poll_interval)

    async def _check_all(self) -> None:
        loop = asyncio.get_running_loop()
        for repo_path in self._tracked_repos:
            try:
                current_head = self.collector.get_head_hash(repo_path)
                cached_head = self._head_cache.get(repo_path.name, "")

                if not current_head or current_head == cached_head:
                    continue

                # first-time seed — not a real change
                if not cached_head:
                    self._head_cache[repo_path.name] = current_head
                    continue

                # genuine change detected
                logger.info("Change in %s: %s → %s", repo_path.name, cached_head[:8], current_head[:8])
                self._head_cache[repo_path.name] = current_head
                self.changes_detected += 1
                self.last_update = datetime.now(UTC).isoformat()

                # re-collect in thread pool so we don't block the event loop
                snapshot = await loop.run_in_executor(None, self.collector.collect_repo, repo_path)

                if self.on_change:
                    await self.on_change({
                        "type": "repo_update",
                        "repo": snapshot.to_dict(),
                        "timestamp": self.last_update,
                    })
            except Exception as e:
                logger.warning("Watcher error for %s: %s", repo_path.name, e)
