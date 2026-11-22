"""URL Validation and SSRF (Server-Side Request Forgery) Defense Module.

Protects RAGShield from being abused to scan unauthorized internal networks,
loopback interfaces, or cloud provider metadata endpoints (e.g., 169.254.169.254).
"""

import ipaddress
import socket
from typing import List, Optional
from urllib.parse import urlparse


class SSRFSecurityError(ValueError):
    """Raised when a target URL violates security boundaries (SSRF attempt)."""
    pass


class InvalidTargetURLError(ValueError):
    """Raised when a target URL is malformed or uses an unsupported scheme."""
    pass


# Well-known dangerous IP addresses/ranges that must always be blocked
BLOCKED_METADATA_IPS = {
    "169.254.169.254",  # AWS EC2 / Azure IMDS / GCP metadata
    "metadata.google.internal",
    "100.100.100.200",  # Alibaba Cloud metadata
}


def validate_target_url(
    url: str,
    allow_local: bool = False,
    allowed_hosts: Optional[List[str]] = None
) -> str:
    """Validates that a target URL is safe for outbound security scanning.
    
    Args:
        url: The candidate URL string (e.g. 'http://127.0.0.1:8001/query').
        allow_local: If True, permits loopback connections (127.0.0.1, localhost) for local testing.
        allowed_hosts: Optional explicit whitelist of hostnames or IP strings.
        
    Returns:
        The validated URL string if safe.
        
    Raises:
        InvalidTargetURLError: If scheme is not http/https or URL is malformed.
        SSRFSecurityError: If the target resolves to a private, loopback, or metadata address without permission.
    """
    if not url or not isinstance(url, str):
        raise InvalidTargetURLError("Target URL cannot be empty.")

    url = url.strip()
    try:
        parsed = urlparse(url)
    except Exception as e:
        raise InvalidTargetURLError(f"Malformed target URL: {e}")

    # Enforce safe protocol scheme
    if parsed.scheme.lower() not in ["http", "https"]:
        raise InvalidTargetURLError(
            f"Unsupported scheme '{parsed.scheme}'. Only 'http' and 'https' are permitted."
        )

    hostname = parsed.hostname
    if not hostname:
        raise InvalidTargetURLError(f"Target URL must contain a valid hostname: {url}")

    hostname_lower = hostname.lower()

    # Explicit check for known cloud metadata hostnames
    if hostname_lower in BLOCKED_METADATA_IPS:
        raise SSRFSecurityError(
            f"Target URL points to blocked cloud metadata endpoint: {hostname}"
        )

    # Check whitelist if provided
    if allowed_hosts and hostname_lower in [h.lower() for h in allowed_hosts]:
        return url

    # Resolve hostname to IP to prevent DNS rebinding or hostname obfuscation
    try:
        resolved_ip_str = socket.gethostbyname(hostname)
        ip = ipaddress.ip_address(resolved_ip_str)
    except socket.gaierror as e:
        raise InvalidTargetURLError(f"Could not resolve hostname '{hostname}': {e}")
    except ValueError as e:
        raise InvalidTargetURLError(f"Resolved address is not a valid IP: {e}")

    # Explicit check against metadata IP directly
    if resolved_ip_str in BLOCKED_METADATA_IPS:
        raise SSRFSecurityError(
            f"Target resolves to blocked cloud metadata IP: {resolved_ip_str}"
        )

    # Loopback checks (127.0.0.0/8, ::1)
    if ip.is_loopback:
        if allow_local:
            return url
        raise SSRFSecurityError(
            f"Loopback target '{resolved_ip_str}' is forbidden unless allow_local=True is explicitly set."
        )

    # Private network checks (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
    if ip.is_private:
        if allow_local:
            return url
        raise SSRFSecurityError(
            f"Private RFC1918 address '{resolved_ip_str}' is blocked by SSRF protection."
        )

    # Link-local checks (169.254.0.0/16) - always blocked
    if ip.is_link_local:
        raise SSRFSecurityError(
            f"Link-local address '{resolved_ip_str}' is strictly forbidden."
        )

    # Multicast and reserved ranges
    if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        raise SSRFSecurityError(
            f"Special-purpose IP address '{resolved_ip_str}' is blocked."
        )

    return url
