"""Target Service for Connectivity and Pre-Flight Health Verifications."""

import json
from typing import Optional
from backend.app.models.target import Target
from backend.app.schemas.target import TargetHealthResponse
from engine.targets.http_adapter import HTTPTargetAdapter


class TargetService:
    """Business logic for target verification and adapter configuration."""

    @staticmethod
    async def verify_connectivity(target: Target) -> TargetHealthResponse:
        """Runs pre-flight health verification and SSRF validation against a target."""
        custom_headers = json.loads(target.custom_headers_json or "{}")
        request_mapping = json.loads(target.request_mapping_json or "{}")
        response_mapping = json.loads(target.response_mapping_json or "{}")

        try:
            adapter = HTTPTargetAdapter(
                target_url=target.target_url,
                api_key=target.api_key,
                custom_headers=custom_headers,
                request_mapping=request_mapping,
                response_mapping=response_mapping,
                allow_local=True,  # Allowed for local targets
                timeout_seconds=5.0
            )

            health = await adapter.check_health()
            return TargetHealthResponse(
                target_id=target.id,
                target_name=target.name,
                target_url=target.target_url,
                is_reachable=health.is_reachable,
                status_code=health.status_code,
                latency_ms=health.latency_ms,
                message=health.message
            )
        except Exception as e:
            return TargetHealthResponse(
                target_id=target.id,
                target_name=target.name,
                target_url=target.target_url,
                is_reachable=False,
                status_code=None,
                latency_ms=0.0,
                message=f"SSRF or connection check failed: {str(e)}"
            )
