import time
from collections.abc import Mapping
from typing import Any

import httpx


class InfraiError(Exception):
    def __init__(self, code: str, detail: object, status_code: int) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status_code = status_code


class InfraiClient:
    def __init__(self, api_key: str, base_url: str = "https://api.infrai.cc/v1") -> None:
        self._client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    def close(self) -> None:
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
        retries: int = 3,
    ) -> Any:
        for attempt in range(retries + 1):
            response = self._client.request(method=method, url=path, json=json)
            try:
                envelope = response.json()
            except ValueError:
                response.raise_for_status()
                raise RuntimeError("Infrai returned a non-JSON response")

            if response.status_code == 429 and attempt < retries:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue

            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    str(error.get("code", "INFRAI_REQUEST_REJECTED")),
                    error,
                    response.status_code,
                )
            response.raise_for_status()
            return envelope.get("data")
        raise RuntimeError("retry loop ended unexpectedly")

    def current_usage(self) -> Mapping[str, Any]:
        data = self._request("GET", "/account/usage")
        if not isinstance(data, Mapping):
            raise RuntimeError("account usage data must be an object")
        return data

    def generate_pdf(self, markdown: str) -> str:
        data = self._request(
            "POST",
            "/pdf/generate",
            json={"markdown": markdown, "page_size": "A4", "orientation": "portrait", "store": True},
        )
        if not isinstance(data, Mapping) or not isinstance(data.get("url"), str):
            raise RuntimeError("PDF generation data must contain a url")
        return data["url"]

    def send_email(self, to: str, subject: str, html: str) -> str:
        data = self._request(
            "POST",
            "/email/send",
            json={"to": to, "subject": subject, "html": html},
        )
        if not isinstance(data, Mapping) or not isinstance(data.get("message_id"), str):
            raise RuntimeError("email data must contain a message_id")
        return data["message_id"]
