import asyncio
import logging

import aiohttp
from aiohttp import ClientSession

_LOGGER = logging.getLogger(__name__)
HOST = "https://neviweb.com"
LOGIN_URL = f"{HOST}/api/login"


class SessionManager:
    _instance = None
    _session: ClientSession | None = None
    _last_used: float | None = None
    _timeout = 600  # 10 minutes in seconds

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def create_session(self) -> ClientSession:
        if self._session is None:
            _LOGGER.debug("Creating new session")
            self._session = aiohttp.ClientSession()
        #            await self.login(username, password)
        else:
            _LOGGER.debug("Reusing existing session")
        self._last_used = asyncio.get_event_loop().time()
        return self._session

    async def login(self, username, password):
        if self._session is None:
            raise ValueError("self._session is None")

        data = {
            "username": username,
            "password": password,
            "interface": "neviweb",
            "stayConnected": 1,
        }
        async with self._session.post(LOGIN_URL, json=data) as response:
            if response.status != 200:
                raise Exception("Cannot log in to Neviweb")
            _LOGGER.debug("Logged in to Neviweb")

    async def keep_alive(self):
        while True:
            await asyncio.sleep(self._timeout - 60)  # Check 1 minute before timeout
            if self._session is None or self._last_used is None:
                raise ValueError("self._session is None")
            if asyncio.get_event_loop().time() - self._last_used >= self._timeout:
                _LOGGER.debug("Session expired, logging in again")
                await self.login(None, None)

    async def close_session(self):
        if self._session is not None:
            await self._session.close()
            self._session = None
            _LOGGER.debug("Neviweb session closed")


session_manager = SessionManager()
