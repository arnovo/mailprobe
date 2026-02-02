"""Minimal mocks for network I/O (DNS and SMTP)."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest


class FakeMXRecord:
    """Fake MX record for testing."""

    def __init__(self, preference: int, exchange: str):
        self.preference = preference
        self.exchange = exchange


class FakeDNSAnswer:
    """Fake DNS answer that can be iterated."""

    def __init__(self, records: list[FakeMXRecord]):
        self._records = records

    def __iter__(self):
        return iter(self._records)


class FakeSMTP:
    """Fake SMTP connection that accepts emails."""

    def __init__(self, host: str, port: int, timeout: int = 30):
        self.host = host
        self.port = port
        self.timeout = timeout
        self._debuglevel = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set_debuglevel(self, level: int):
        self._debuglevel = level

    def ehlo_or_helo_if_needed(self):
        pass

    def ehlo(self):
        return (250, b"OK")

    def mail(self, sender: str):
        return (250, b"OK")

    def rcpt(self, recipient: str) -> tuple[int, bytes]:
        """Accept all recipients by default."""
        return (250, b"2.1.5 OK")

    def quit(self):
        pass


class FakeSMTPReject(FakeSMTP):
    """Fake SMTP connection that rejects emails."""

    def rcpt(self, recipient: str) -> tuple[int, bytes]:
        return (550, b"5.1.1 User unknown")


class FakeSMTPCatchAll(FakeSMTP):
    """Fake SMTP connection that accepts all emails (catch-all)."""

    def rcpt(self, recipient: str) -> tuple[int, bytes]:
        # Always accept, even random addresses
        return (250, b"2.1.5 OK")


class FakeSMTPTimeout(FakeSMTP):
    """Fake SMTP connection that times out."""

    def __init__(self, *args, **kwargs):
        raise TimeoutError("Connection timed out")


@pytest.fixture
def mock_dns_valid(monkeypatch):
    """Mock DNS resolver to return valid MX records."""

    def fake_resolve(domain: str, rdtype: str, lifetime: float = None):
        if rdtype == "MX":
            record = FakeMXRecord(10, f"mail.{domain}.")
            return FakeDNSAnswer([record])
        if rdtype == "A":
            # Return a fake IP
            mock = MagicMock()
            mock.__iter__ = lambda self: iter(["93.184.216.34"])
            return mock
        if rdtype == "TXT":
            # Return SPF record
            mock = MagicMock()
            mock.__iter__ = lambda self: iter(['"v=spf1 include:_spf.google.com ~all"'])
            return mock
        raise Exception(f"Unexpected rdtype: {rdtype}")

    monkeypatch.setattr("dns.resolver.resolve", fake_resolve)


@pytest.fixture
def mock_dns_no_mx(monkeypatch):
    """Mock DNS resolver to return no MX records."""
    import dns.resolver

    def fake_resolve(domain: str, rdtype: str, lifetime: float = None):
        if rdtype == "MX":
            raise dns.resolver.NoAnswer()
        raise dns.resolver.NXDOMAIN()

    monkeypatch.setattr("dns.resolver.resolve", fake_resolve)


@pytest.fixture
def mock_smtp_valid(monkeypatch):
    """Mock SMTP to accept emails."""
    monkeypatch.setattr("smtplib.SMTP", FakeSMTP)


@pytest.fixture
def mock_smtp_reject(monkeypatch):
    """Mock SMTP to reject emails."""
    monkeypatch.setattr("smtplib.SMTP", FakeSMTPReject)


@pytest.fixture
def mock_smtp_catch_all(monkeypatch):
    """Mock SMTP to behave as catch-all."""
    monkeypatch.setattr("smtplib.SMTP", FakeSMTPCatchAll)


@pytest.fixture
def mock_smtp_timeout(monkeypatch):
    """Mock SMTP to timeout."""
    monkeypatch.setattr("smtplib.SMTP", FakeSMTPTimeout)


@pytest.fixture
def mock_network(mock_dns_valid, mock_smtp_valid):
    """Combine DNS and SMTP mocks for full network isolation."""
    pass
