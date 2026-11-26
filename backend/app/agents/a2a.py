"""Typed Agent2Agent (A2A) message bus and live SSE fan-out broadcaster."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from ..models import A2AMessage


class SSEBroadcaster:
    """Thread-safe async pub/sub broadcaster pushing live A2A hops to /api/stream clients."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=128)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(q)

    def publish_sync(self, payload: dict[str, Any]) -> None:
        for q in list(self._subscribers):
            if q.full():
                try:
                    q.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass


broadcaster = SSEBroadcaster()


def make_a2a_hop(
    trace_id: str,
    from_agent: str,
    to_agent: str,
    action: str,
    payload: dict[str, Any],
    latency_ms: float,
) -> A2AMessage:
    msg = A2AMessage(
        trace_id=trace_id,
        from_agent=from_agent,
        to_agent=to_agent,
        action=action,
        payload=payload,
        latency_ms=round(latency_ms, 2),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    broadcaster.publish_sync({"type": "a2a_hop", "data": msg.model_dump()})
    return msg
