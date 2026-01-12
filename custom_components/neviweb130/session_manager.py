import asyncio
import logging

import aiohttp
from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)


class SessionManager:
    _session: ClientSession | None = None
    _last_used: float | None = None
    _timeout = 600  # 10 minutes in seconds

    def __init__(self):
        self._session: aiohttp.ClientSession | None = None

    async def create_session(self) -> aiohttp.ClientSession:
        # If session exists but is closed → reset it
        if self._session is not None:
            if self._session.closed:
                _LOGGER.debug("Session was closed, creating a new one")
                self._session = None
            else:
                _LOGGER.debug("Reusing existing session")
                return self._session

        # Create new session
        _LOGGER.debug("Creating new session")
        timeout = aiohttp.ClientTimeout(total=30)
        self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close_session(self):
        if self._session is not None:
            try:
                await self._session.close()
            except Exception as e:
                _LOGGER.error("Error closing session: %s", e)
            finally:
                _LOGGER.debug("Neviweb session closed and reset")
                self._session = None
