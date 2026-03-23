"""SSE pub/sub — centralized Server-Sent Events notification system."""

import asyncio

# In-memory pub/sub (replace with Redis pub/sub in production)
_listeners: dict[str, list[asyncio.Queue]] = {}


def notify(company_id: str, event: dict) -> None:
    """Notify all SSE listeners for a company."""
    for queue in _listeners.get(company_id, []):
        queue.put_nowait(event)


def subscribe(company_id: str) -> asyncio.Queue:
    """Subscribe to SSE events for a company. Returns a queue."""
    queue: asyncio.Queue = asyncio.Queue()
    if company_id not in _listeners:
        _listeners[company_id] = []
    _listeners[company_id].append(queue)
    return queue


def unsubscribe(company_id: str, queue: asyncio.Queue) -> None:
    """Unsubscribe from SSE events."""
    if company_id in _listeners:
        _listeners[company_id].remove(queue)
        if not _listeners[company_id]:
            del _listeners[company_id]
