"""DNS operations: MX lookup, SPF/DMARC check, hostname resolution."""
from __future__ import annotations

import socket

import dns.resolver

from app.core.config import settings

DNS_TIMEOUT_SECS = getattr(settings, "dns_timeout_seconds", 5.0)


def mx_lookup(domain: str, dns_timeout_seconds: float | None = None) -> list[tuple[int, str]]:
    """
    Returns list of (preference, exchange) sorted by preference.
    
    Raises:
        dns.resolver.NXDOMAIN: Domain does not exist
        dns.resolver.NoAnswer: No MX records
        dns.resolver.Timeout: DNS query timed out
    """
    timeout = dns_timeout_seconds if dns_timeout_seconds is not None else DNS_TIMEOUT_SECS
    answers = dns.resolver.resolve(domain, "MX", lifetime=timeout)
    mx = []
    for r in answers:
        mx.append((int(r.preference), str(r.exchange).rstrip(".")))
    mx.sort(key=lambda x: x[0])
    return mx


def resolve_to_ip(host: str, dns_timeout_seconds: float | None = None) -> str | None:
    """
    Resolve hostname to IP with timeout.
    Returns IP if host is already an IP or resolution succeeds, None otherwise.
    """
    timeout = dns_timeout_seconds if dns_timeout_seconds is not None else DNS_TIMEOUT_SECS
    host = host.rstrip(".")
    if not host:
        return None

    # Check if already an IPv4 address
    try:
        socket.inet_pton(socket.AF_INET, host)
        return host
    except OSError:
        pass

    # Check if already an IPv6 address
    try:
        socket.inet_pton(socket.AF_INET6, host)
        return host
    except OSError:
        pass

    # Try to resolve A record
    try:
        answers = dns.resolver.resolve(host, "A", lifetime=timeout)
        for r in answers:
            return str(r)
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        pass
    except dns.resolver.NoNameservers:
        pass

    # Try to resolve AAAA record
    try:
        answers = dns.resolver.resolve(host, "AAAA", lifetime=timeout)
        for r in answers:
            return str(r)
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        pass
    except dns.resolver.NoNameservers:
        pass

    return None


def check_domain_spf_dmarc(domain: str, dns_timeout_seconds: float | None = None) -> tuple[bool, bool]:
    """
    Check if domain has SPF (TXT with v=spf1) and DMARC (_dmarc with v=DMARC1).
    Returns (has_spf, has_dmarc). Does not block if lookup fails.
    """
    timeout = dns_timeout_seconds if dns_timeout_seconds is not None else DNS_TIMEOUT_SECS
    has_spf, has_dmarc = False, False

    # Check SPF
    try:
        answers = dns.resolver.resolve(domain, "TXT", lifetime=timeout)
        for r in answers:
            txt = str(r).lower()
            if "v=spf1" in txt:
                has_spf = True
                break
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        pass
    except dns.resolver.NoNameservers:
        pass

    # Check DMARC
    try:
        answers = dns.resolver.resolve(f"_dmarc.{domain}", "TXT", lifetime=timeout)
        for r in answers:
            txt = str(r).lower()
            if "v=dmarc1" in txt:
                has_dmarc = True
                break
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.Timeout):
        pass
    except dns.resolver.NoNameservers:
        pass

    return has_spf, has_dmarc
