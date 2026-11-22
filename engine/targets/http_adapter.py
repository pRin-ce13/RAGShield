"""Asynchronous HTTP Target Adapter for RAGShield.

Connects to arbitrary HTTP/REST RAG target endpoints with built-in SSRF protection,
configurable timeouts, field mapping, authentication injection, and latency profiling.
"""

import time
from typing import Any, Dict, List, Optional
import httpx

from .base import BaseTargetAdapter, TargetHealth, TargetResponse
from .url_validator import validate_target_url


class HTTPTargetAdapter(BaseTargetAdapter):
    """Universal asynchronous HTTP adapter for RAG targets."""

    def __init__(
        self,
        target_name: str,
        base_url: str,
        query_path: str = "/query",
        health_path: str = "/health",
        api_key: Optional[str] = None,
        auth_header: str = "X-API-Key",
        auth_type: str = "header",  # 'header', 'bearer', or 'none'
        timeout_seconds: float = 10.0,
        allow_local: bool = False,
        allowed_hosts: Optional[List[str]] = None,
        request_field_map: Optional[Dict[str, str]] = None,
        response_field_map: Optional[Dict[str, str]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
        client: Optional[httpx.AsyncClient] = None
    ):
        """Initializes and validates the HTTP Target Adapter.
        
        Args:
            target_name: Name of the target application.
            base_url: Base URL of the target service (e.g. 'http://127.0.0.1:8001').
            query_path: Endpoint path for submitting questions.
            health_path: Endpoint path for checking service health.
            api_key: Optional secret credential for the target.
            auth_header: Header name for the API key (default: 'X-API-Key').
            auth_type: Type of authentication ('header', 'bearer', 'none').
            timeout_seconds: Maximum seconds before timing out requests.
            allow_local: Whether to permit scanning loopback/private addresses.
            allowed_hosts: Whitelist of permitted hostnames.
            request_field_map: Mapping for outgoing fields (e.g. {'question': 'prompt'}).
            response_field_map: Mapping for incoming fields (e.g. {'answer': 'output'}).
            extra_headers: Additional static HTTP headers.
            client: Optional pre-configured httpx.AsyncClient (useful for testing).
        """
        self._target_name = target_name
        self._base_url = base_url.rstrip("/")
        self.query_path = query_path.strip("/")
        self.health_path = health_path.strip("/")
        self.api_key = api_key
        self.auth_header = auth_header
        self.auth_type = auth_type.lower()
        self.timeout_seconds = timeout_seconds
        self.allow_local = allow_local
        self.allowed_hosts = allowed_hosts
        self.extra_headers = extra_headers or {}
        self._custom_client = client

        # 1. Enforce SSRF boundary validation immediately on adapter initialization
        self._full_query_url = f"{self._base_url}/{self.query_path}"
        validate_target_url(
            self._full_query_url,
            allow_local=self.allow_local,
            allowed_hosts=self.allowed_hosts
        )

        # Field translation maps
        self.request_field_map = request_field_map or {
            "question": "question",
            "role": "role",
            "top_k": "top_k"
        }
        self.response_field_map = response_field_map or {
            "answer": "answer",
            "sources": "sources"
        }

    @property
    def target_name(self) -> str:
        return self._target_name

    @property
    def target_url(self) -> str:
        return self._base_url

    def _build_headers(self) -> Dict[str, str]:
        """Constructs headers including authentication credentials."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "RAGShield-Security-Scanner/1.0",
            **self.extra_headers
        }

        if self.api_key:
            if self.auth_type == "bearer":
                headers["Authorization"] = f"Bearer {self.api_key}"
            elif self.auth_type == "header":
                headers[self.auth_header] = self.api_key

        return headers

    def _get_client(self) -> httpx.AsyncClient:
        """Returns the configured AsyncClient or creates a fresh one."""
        if self._custom_client is not None:
            return self._custom_client
        return httpx.AsyncClient(timeout=httpx.Timeout(self.timeout_seconds))

    async def check_health(self) -> TargetHealth:
        """Performs a health check against the target's health endpoint."""
        health_url = f"{self._base_url}/{self.health_path}"
        headers = self._build_headers()
        start_time = time.perf_counter()

        client = self._get_client()
        should_close = self._custom_client is None

        try:
            response = await client.get(health_url, headers=headers)
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            
            try:
                body = response.json()
            except Exception:
                body = {"raw": response.text}

            is_healthy = response.status_code == 200
            return TargetHealth(
                is_healthy=is_healthy,
                status_code=response.status_code,
                latency_ms=elapsed_ms,
                details=body if isinstance(body, dict) else {"content": body}
            )

        except httpx.TimeoutException as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return TargetHealth(
                is_healthy=False,
                status_code=504,
                latency_ms=elapsed_ms,
                error=f"Health check timed out after {self.timeout_seconds}s: {e}"
            )
        except httpx.ConnectError as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return TargetHealth(
                is_healthy=False,
                status_code=503,
                latency_ms=elapsed_ms,
                error=f"Connection refused or target host unreachable: {e}"
            )
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return TargetHealth(
                is_healthy=False,
                status_code=500,
                latency_ms=elapsed_ms,
                error=f"Unexpected health check error: {e}"
            )
        finally:
            if should_close:
                await client.aclose()

    async def send_query(
        self,
        question: str,
        role: Optional[str] = None,
        **kwargs
    ) -> TargetResponse:
        """Executes a query against the target RAG service."""
        # 1. Translate outgoing request payload using field mapping
        payload: Dict[str, Any] = {
            self.request_field_map.get("question", "question"): question
        }
        if role is not None:
            payload[self.request_field_map.get("role", "role")] = role

        for k, v in kwargs.items():
            mapped_key = self.request_field_map.get(k, k)
            payload[mapped_key] = v

        headers = self._build_headers()
        start_time = time.perf_counter()

        client = self._get_client()
        should_close = self._custom_client is None

        try:
            response = await client.post(
                self._full_query_url,
                json=payload,
                headers=headers
            )
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

            try:
                raw_data = response.json()
            except Exception:
                raw_data = {"text": response.text}

            # 2. Extract answer and sources using response field map
            answer_field = self.response_field_map.get("answer", "answer")
            sources_field = self.response_field_map.get("sources", "sources")

            answer = ""
            sources: List[str] = []
            if isinstance(raw_data, dict):
                answer = str(raw_data.get(answer_field, ""))
                raw_sources = raw_data.get(sources_field, [])
                if isinstance(raw_sources, list):
                    sources = [str(s) for s in raw_sources]
            else:
                answer = response.text

            error_msg = None
            if not (200 <= response.status_code < 300):
                error_msg = f"Target returned HTTP {response.status_code}: {answer or raw_data}"

            return TargetResponse(
                status_code=response.status_code,
                answer=answer,
                raw_response=raw_data if isinstance(raw_data, dict) else {"raw": raw_data},
                response_time_ms=elapsed_ms,
                sources=sources,
                error=error_msg
            )

        except httpx.TimeoutException as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return TargetResponse(
                status_code=504,
                answer="",
                response_time_ms=elapsed_ms,
                error=f"Target request timed out after {self.timeout_seconds}s: {e}"
            )
        except httpx.ConnectError as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return TargetResponse(
                status_code=503,
                answer="",
                response_time_ms=elapsed_ms,
                error=f"Connection refused connecting to target: {e}"
            )
        except Exception as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return TargetResponse(
                status_code=500,
                answer="",
                response_time_ms=elapsed_ms,
                error=f"Target communication error: {e}"
            )
        finally:
            if should_close:
                await client.aclose()
