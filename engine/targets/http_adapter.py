"""Asynchronous HTTP Target Adapter for RAGShield.

Connects to arbitrary HTTP/REST RAG target endpoints with built-in SSRF protection,
configurable timeouts, field mapping, authentication injection, and latency profiling.
"""

import asyncio
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
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
        parsed = urlparse(base_url)
        # Normalize: if caller passed endpoint path in base_url (e.g. http://127.0.0.1:8001/query)
        if parsed.path and parsed.path.rstrip("/") in ["/query", "/chat", "/v1/query", "/ask"]:
            self._base_url = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")
            self.query_path = parsed.path.lstrip("/")
        else:
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
            if response.status_code == 404:
                parsed = urlparse(self._base_url)
                fallback_url = f"{parsed.scheme}://{parsed.netloc}/{self.health_path}"
                if fallback_url != health_url:
                    try:
                        fallback_res = await client.get(fallback_url, headers=headers)
                        if fallback_res.status_code == 200:
                            response = fallback_res
                    except Exception:
                        pass

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

    async def send_multi_turn_query(
        self,
        turns: List[Any],
        role: Optional[str] = None,
        **kwargs
    ) -> TargetResponse:
        """Sends a sequential series of conversational turns to the target RAG service.
        
        Maintains rolling dialogue history across turns and attaches all intermediate
        turn responses to the final TargetResponse object.
        """
        if not turns:
            return TargetResponse(
                status_code=400,
                answer="",
                error="No conversational turns provided."
            )

        turn_responses: List[Dict[str, Any]] = []
        messages_history: List[Dict[str, str]] = []
        last_response: Optional[TargetResponse] = None

        for idx, turn in enumerate(turns):
            # Extract turn payload and role
            if hasattr(turn, "payload"):
                turn_payload = turn.payload
                turn_role = getattr(turn, "target_role", None) or role
            elif isinstance(turn, dict):
                turn_payload = turn.get("payload", "")
                turn_role = turn.get("target_role") or role
            else:
                turn_payload = str(turn)
                turn_role = role

            # Execute turn query including rolling history
            turn_res = await self.send_query(
                question=turn_payload,
                role=turn_role,
                messages=messages_history.copy(),
                **kwargs
            )
            last_response = turn_res

            # Record turn telemetry
            turn_responses.append({
                "turn_index": idx,
                "payload": turn_payload,
                "role": turn_role,
                "status_code": turn_res.status_code,
                "answer": turn_res.answer,
                "sources": turn_res.sources,
                "latency_ms": turn_res.response_time_ms,
                "error": turn_res.error
            })

            # Append to rolling conversation history
            messages_history.append({"role": "user", "content": turn_payload})
            if turn_res.answer:
                messages_history.append({"role": "assistant", "content": turn_res.answer})

        if last_response is None:
            return TargetResponse(status_code=500, answer="", error="Multi-turn execution yielded no response.")

        # Attach all turn responses to the final TargetResponse
        last_response.turn_responses = turn_responses
        return last_response

    async def send_stress_probe(
        self,
        question: str,
        concurrency: int = 10,
        role: Optional[str] = None,
        **kwargs
    ) -> TargetResponse:
        """Fires a high-concurrency burst of requests to evaluate target rate-limiting and resilience."""
        start_burst = time.perf_counter()

        tasks = [
            self.send_query(question=question, role=role, **kwargs)
            for _ in range(concurrency)
        ]

        raw_results = await asyncio.gather(*tasks, return_exceptions=True)
        burst_elapsed_ms = round((time.perf_counter() - start_burst) * 1000, 2)

        successful_count = 0
        rate_limited_count = 0
        server_error_count = 0
        network_error_count = 0
        latencies: List[float] = []
        status_codes: List[int] = []

        for item in raw_results:
            if isinstance(item, Exception):
                network_error_count += 1
                status_codes.append(500)
            elif isinstance(item, TargetResponse):
                status_codes.append(item.status_code)
                latencies.append(item.response_time_ms)
                if 200 <= item.status_code < 300:
                    successful_count += 1
                elif item.status_code == 429:
                    rate_limited_count += 1
                elif item.status_code >= 500:
                    server_error_count += 1
                else:
                    successful_count += 1

        avg_latency = round(sum(latencies) / len(latencies), 2) if latencies else 0.0
        max_latency = round(max(latencies), 2) if latencies else 0.0

        summary_answer = (
            f"Stress burst completed in {burst_elapsed_ms}ms with {concurrency} concurrent requests. "
            f"Success: {successful_count}, Rate-Limited (429): {rate_limited_count}, "
            f"Server Errors (5xx): {server_error_count}, Network Failures: {network_error_count}. "
            f"Avg Latency: {avg_latency}ms, Max Latency: {max_latency}ms."
        )

        overall_status = 200
        if server_error_count > 0:
            overall_status = 500
        elif rate_limited_count > 0:
            overall_status = 429

        return TargetResponse(
            status_code=overall_status,
            answer=summary_answer,
            raw_response={
                "concurrency": concurrency,
                "burst_duration_ms": burst_elapsed_ms,
                "success_count": successful_count,
                "rate_limited_count": rate_limited_count,
                "server_error_count": server_error_count,
                "network_error_count": network_error_count,
                "avg_latency_ms": avg_latency,
                "max_latency_ms": max_latency,
                "status_codes": status_codes
            },
            response_time_ms=burst_elapsed_ms,
            sources=[],
            error=f"{server_error_count} server errors detected during stress burst." if server_error_count > 0 else None
        )
