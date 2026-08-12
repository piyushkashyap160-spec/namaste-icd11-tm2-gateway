from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

import requests
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

WHO_API_MAX_RETRIES = int(os.getenv("WHO_API_MAX_RETRIES", "3"))
WHO_API_RETRY_BACKOFF_BASE = float(os.getenv("WHO_API_RETRY_BACKOFF_BASE", "0.5"))


class WHOICDClient:
    """
    Client for the WHO ICD-11 API v2.

    Credentials are loaded only from environment variables.
    The access token is kept in memory and is never returned
    to the frontend.
    """

    def __init__(self) -> None:
        self.client_id = os.getenv("WHO_CLIENT_ID")
        self.client_secret = os.getenv("WHO_CLIENT_SECRET")

        self.base_url = os.getenv(
            "WHO_API_BASE_URL",
            "https://id.who.int",
        ).rstrip("/")

        self.token_url = os.getenv(
            "WHO_TOKEN_URL",
            "https://icdaccessmanagement.who.int/connect/token",
        )

        self.api_version = os.getenv(
            "WHO_API_VERSION",
            "v2",
        )

        self.language = os.getenv(
            "WHO_LANGUAGE",
            "en",
        )

        self._access_token: Optional[str] = None
        self._token_expires_at: float = 0.0

        if not self.client_id:
            raise RuntimeError("WHO_CLIENT_ID is not configured.")

        if not self.client_secret:
            raise RuntimeError("WHO_CLIENT_SECRET is not configured.")

    def _get_access_token(self) -> str:
        """
        Obtain a WHO OAuth access token.

        The token is cached in memory until shortly before expiry.
        """

        now = time.time()

        if (
            self._access_token
            and now < self._token_expires_at - 60
        ):
            return self._access_token

        response = requests.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "icdapi_access",
            },
            timeout=30,
        )

        response.raise_for_status()

        payload = response.json()

        access_token = payload.get("access_token")

        if not access_token:
            raise RuntimeError(
                "WHO authentication succeeded but no access token was returned."
            )

        expires_in = int(payload.get("expires_in", 3600))

        self._access_token = access_token
        self._token_expires_at = now + expires_in

        return access_token

    def _headers(self) -> dict[str, str]:
        """
        Build headers required by WHO ICD API v2.
        """

        token = self._get_access_token()

        return {
            "Authorization": f"Bearer {token}",
            "API-Version": self.api_version,
            "Accept-Language": self.language,
            "Accept": "application/json",
        }

    def get(self, path: str) -> Any:
        """
        Perform an authenticated GET request against the WHO API.

        Transient failures (network errors, 5xx responses) are retried
        with exponential backoff, up to WHO_API_MAX_RETRIES attempts.
        Client errors (4xx, e.g. bad path or auth failure) are NOT
        retried, since retrying will not fix them and doing so risks
        masking a real bug as a transient glitch.
        """

        if not path.startswith("/"):
            path = "/" + path

        url = f"{self.base_url}{path}"

        last_exc: Optional[Exception] = None

        for attempt in range(1, WHO_API_MAX_RETRIES + 1):
            try:
                response = requests.get(
                    url,
                    headers=self._headers(),
                    timeout=30,
                )

                if 400 <= response.status_code < 500:
                    # Client errors are not retried.
                    response.raise_for_status()

                response.raise_for_status()
                return response.json()

            except requests.RequestException as exc:
                last_exc = exc
                is_client_error = (
                    isinstance(exc, requests.HTTPError)
                    and exc.response is not None
                    and 400 <= exc.response.status_code < 500
                )

                if is_client_error:
                    logger.error(
                        "WHO API client error (not retried): %s %s",
                        path,
                        exc.response.status_code,
                    )
                    raise

                is_last_attempt = attempt == WHO_API_MAX_RETRIES

                if is_last_attempt:
                    logger.error(
                        "WHO API request failed after %d attempts: %s (%s)",
                        attempt,
                        path,
                        exc.__class__.__name__,
                    )
                    raise

                backoff = WHO_API_RETRY_BACKOFF_BASE * (2 ** (attempt - 1))
                logger.warning(
                    "WHO API request failed (attempt %d/%d) for %s: %s; retrying in %.1fs",
                    attempt,
                    WHO_API_MAX_RETRIES,
                    path,
                    exc.__class__.__name__,
                    backoff,
                )
                time.sleep(backoff)

        raise last_exc  # type: ignore[misc]

    def get_entity(self, entity_id: str) -> Any:
        """
        Retrieve an ICD entity by its WHO entity ID.

        Example:
            client.get_entity("107294155")
        """

        entity_id = entity_id.strip()

        if not entity_id:
            raise ValueError("entity_id cannot be empty.")

        path = f"/icd/entity/{entity_id}"

        return self.get(path)

    def health_check(self) -> dict[str, Any]:
        """
        Verify that authentication and a WHO API request work.

        Returns only safe diagnostic information.
        """

        try:
            token = self._get_access_token()

            return {
                "connected": True,
                "authenticated": bool(token),
                "api_base_url": self.base_url,
                "api_version": self.api_version,
                "language": self.language,
            }

        except Exception as exc:
            return {
                "connected": False,
                "authenticated": False,
                "api_base_url": self.base_url,
                "api_version": self.api_version,
                "language": self.language,
                "error": str(exc),
            }


who_icd_client = WHOICDClient()
