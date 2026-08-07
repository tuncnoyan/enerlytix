"""Shared security helpers for API authorization, redirect safety, and runtime hardening."""

from __future__ import annotations

import ipaddress
from typing import Iterable, List
from urllib.parse import urlsplit

from django.conf import settings
from rest_framework.response import Response


def api_unauthenticated_response(detail: str = "Authentication credentials were not provided.") -> Response:
    """Return a normalized 401 response for unauthenticated API requests."""

    return Response({"detail": detail}, status=401)


def api_forbidden_response(detail: str = "You do not have permission to perform this action.") -> Response:
    """Return a normalized 403 response for authenticated-but-unauthorized API requests."""

    return Response({"detail": detail}, status=403)


def ensure_api_authenticated(request) -> Response | None:
    """Return 401 response when request user is not authenticated, else None."""

    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return api_unauthenticated_response()
    return None


def parse_trusted_proxy_cidrs(raw_values: Iterable[str]) -> List[ipaddress._BaseNetwork]:
    """Parse configured proxy CIDR values, ignoring invalid entries."""

    networks: List[ipaddress._BaseNetwork] = []
    for raw in raw_values:
        token = str(raw or "").strip()
        if not token:
            continue
        try:
            networks.append(ipaddress.ip_network(token, strict=False))
        except ValueError:
            continue
    return networks


def configured_trusted_proxy_networks() -> List[ipaddress._BaseNetwork]:
    """Return configured trusted proxy CIDRs from Django settings."""

    raw = getattr(settings, "TRUSTED_PROXY_CIDRS", [])
    if isinstance(raw, str):
        raw = [part.strip() for part in raw.split(",")]
    return parse_trusted_proxy_cidrs(raw)


def is_remote_addr_trusted_proxy(remote_addr: str | None) -> bool:
    """Return whether the direct client IP is inside a trusted proxy CIDR allowlist."""

    if not remote_addr:
        return False
    try:
        remote_ip = ipaddress.ip_address(str(remote_addr).strip())
    except ValueError:
        return False

    for network in configured_trusted_proxy_networks():
        if remote_ip in network:
            return True
    return False


def resolve_request_client_ip(request) -> str | None:
    """Resolve client IP, trusting X-Forwarded-For only via trusted proxies."""

    remote_addr = (request.META.get("REMOTE_ADDR") or "").strip()
    if not is_remote_addr_trusted_proxy(remote_addr):
        return remote_addr or None

    forwarded_for = (request.META.get("HTTP_X_FORWARDED_FOR") or "").strip()
    if forwarded_for:
        first_hop = forwarded_for.split(",")[0].strip()
        if first_hop:
            return first_hop
    return remote_addr or None


def is_safe_internal_redirect_target(target: str) -> bool:
    """Allow only local, absolute-path redirects and reject external/scheme-relative targets."""

    candidate = str(target or "").strip()
    if not candidate:
        return False
    if not candidate.startswith("/"):
        return False
    if candidate.startswith("//"):
        return False

    parsed = urlsplit(candidate)
    if parsed.scheme or parsed.netloc:
        return False
    return True


def production_security_issues() -> List[str]:
    """Return a list of production security posture violations."""

    issues: List[str] = []

    secret_key = str(getattr(settings, "SECRET_KEY", "") or "")
    if (not secret_key) or secret_key.startswith("django-insecure-") or secret_key == "django-insecure-change-me-in-production":
        issues.append("SECRET_KEY must not use default/insecure placeholder value")

    if getattr(settings, "DEBUG", False):
        issues.append("DEBUG must be False in production")

    if not getattr(settings, "SECURE_SSL_REDIRECT", False):
        issues.append("SECURE_SSL_REDIRECT must be True in production")

    if not getattr(settings, "SESSION_COOKIE_SECURE", False):
        issues.append("SESSION_COOKIE_SECURE must be True in production")

    if not getattr(settings, "CSRF_COOKIE_SECURE", False):
        issues.append("CSRF_COOKIE_SECURE must be True in production")

    if int(getattr(settings, "SECURE_HSTS_SECONDS", 0) or 0) <= 0:
        issues.append("SECURE_HSTS_SECONDS must be greater than 0 in production")

    return issues


def validate_production_security_posture_or_raise() -> None:
    """Raise RuntimeError when configured production posture requirements are unmet."""

    issues = production_security_issues()
    if issues:
        issue_summary = "; ".join(issues)
        raise RuntimeError(f"Production security posture validation failed: {issue_summary}")
