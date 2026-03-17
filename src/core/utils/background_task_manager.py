"""
Background Task Manager - Manages async and sync long-running tasks in separate threads.
Prevents blocking of main request handler threads.
"""

import asyncio
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Awaitable, Callable, Optional

logger = logging.getLogger(__name__)


class BackgroundTaskManager:
    """
    Manages background tasks using thread pools.
    Supports both sync and async tasks without blocking the main thread.
    """

    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize the background task manager.
        
        Args:
            max_workers: Maximum number of worker threads. 
                         If None, defaults to (number of CPUs * 5)
        """
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.daemon_threads = []
        logger.info(
            f"BackgroundTaskManager initialized with max_workers={max_workers}"
        )

    def add_task(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """
        Add a sync function to run in the background thread pool.
        
        Args:
            func: Synchronous function to execute
            *args: Positional arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
        """
        try:
            self.executor.submit(self._run_sync_task, func, args, kwargs)
            logger.debug(f"Added sync task: {func.__name__}")
        except Exception as e:
            logger.error(f"Failed to add sync task: {e}", exc_info=True)

    def add_async_task(
        self,
        coro: Awaitable,
    ) -> None:
        """
        Add an async coroutine to run in a background thread.
        
        Args:
            coro: Async coroutine to execute
        """
        try:
            self.executor.submit(self._run_async_task, coro)
            logger.debug("Added async task to background executor")
        except Exception as e:
            logger.error(f"Failed to add async task: {e}", exc_info=True)

    @staticmethod
    def _run_sync_task(func: Callable, args: tuple, kwargs: dict) -> None:
        """
        Run a synchronous task in the background.
        
        Args:
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments
        """
        try:
            logger.info(f"Starting background task: {func.__name__}")
            func(*args, **kwargs)
            logger.info(f"Completed background task: {func.__name__}")
        except Exception as e:
            logger.error(
                f"Error in background task {func.__name__}: {e}", exc_info=True
            )

    @staticmethod
    def _run_async_task(coro: Awaitable) -> None:
        """
        Run an async coroutine in the background with its own event loop.
        
        Args:
            coro: Async coroutine to execute
        """
        try:
            logger.info("Starting background async task")
            # Use asyncio.run() which properly handles event loop lifecycle
            # and cleanup, especially important for async libraries like motor
            asyncio.run(coro)
            logger.info("Completed background async task")
        except Exception as e:
            logger.error(f"Error in background async task: {e}", exc_info=True)

    def add_task_daemon(
        self,
        func: Callable,
        *args: Any,
        **kwargs: Any,
    ) -> threading.Thread:
        """
        Add a task to run as a daemon thread (will terminate when main thread exits).
        Useful for fire-and-forget operations.
        
        Args:
            func: Synchronous function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            threading.Thread: The daemon thread created
        """
        thread = threading.Thread(
            target=self._run_sync_task, args=(func, args, kwargs), daemon=True
        )
        thread.start()
        self.daemon_threads.append(thread)
        logger.debug(f"Added daemon task: {func.__name__}")
        return thread

    def add_async_task_daemon(self, coro: Awaitable) -> threading.Thread:
        """
        Add an async task to run as a daemon thread.
        
        Args:
            coro: Async coroutine to execute
            
        Returns:
            threading.Thread: The daemon thread created
        """
        thread = threading.Thread(
            target=self._run_async_task, args=(coro,), daemon=True
        )
        thread.start()
        self.daemon_threads.append(thread)
        logger.debug("Added daemon async task")
        return thread

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the thread pool executor.
        
        Args:
            wait: If True, wait for all pending tasks to complete
        """
        logger.info("Shutting down BackgroundTaskManager")
        self.executor.shutdown(wait=wait)
        
        # Wait for daemon threads to finish if requested
        if wait:
            for thread in self.daemon_threads:
                thread.join(timeout=5)
        
        logger.info("BackgroundTaskManager shutdown complete")


# Global instance
_background_task_manager: Optional[BackgroundTaskManager] = None


def get_background_task_manager(
    max_workers: Optional[int] = None,
) -> BackgroundTaskManager:
    """
    Get or create the global background task manager instance.
    
    Args:
        max_workers: Maximum number of worker threads (only used on first call)
        
    Returns:
        BackgroundTaskManager: The global instance
    """
    global _background_task_manager
    if _background_task_manager is None:
        _background_task_manager = BackgroundTaskManager(max_workers=max_workers)
    return _background_task_manager


def shutdown_background_task_manager(wait: bool = True) -> None:
    """
    Shutdown the global background task manager.
    
    Args:
        wait: If True, wait for all pending tasks to complete
    """
    global _background_task_manager
    if _background_task_manager is not None:
        _background_task_manager.shutdown(wait=wait)
        _background_task_manager = None
