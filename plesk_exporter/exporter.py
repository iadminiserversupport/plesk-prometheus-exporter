"""Plesk REST API Prometheus collector."""
from __future__ import annotations
import os, time
from dataclasses import dataclass
from typing import Any
import requests
from prometheus_client import REGISTRY, start_http_server
from prometheus_client.core import GaugeMetricFamily

@dataclass(frozen=True)
class Config:
    base_url: str
    api_key: str
    verify_ssl: bool = True
    timeout: float = 10.0
    @classmethod
    def from_env(cls) -> "Config":
        base_url = os.getenv("PLESK_URL", "").rstrip("/")
        api_key = os.getenv("PLESK_API_KEY", "")
        if not base_url: raise ValueError("PLESK_URL is required")
        if not api_key: raise ValueError("PLESK_API_KEY is required")
        verify_ssl = os.getenv("PLESK_VERIFY_SSL", "true").lower() not in {"0","false","no","off"}
        try: timeout = float(os.getenv("PLESK_TIMEOUT", "10"))
        except ValueError as exc: raise ValueError("PLESK_TIMEOUT must be a number") from exc
        if timeout <= 0: raise ValueError("PLESK_TIMEOUT must be greater than zero")
        return cls(base_url, api_key, verify_ssl, timeout)

class PleskAPI:
    """Read-only client for the Plesk REST API."""
    def __init__(self, config: Config, session: requests.Session | None = None):
        self.config = config
        self.session = session or requests.Session()
        self.session.headers.update({"Accept":"application/json","Content-Type":"application/json","X-API-Key":config.api_key})
    def get_json(self, endpoint: str) -> Any:
        url = f"{self.config.base_url}/api/v2/{endpoint.lstrip('/')}"
        response = self.session.get(url, timeout=self.config.timeout, verify=self.config.verify_ssl)
        response.raise_for_status()
        return response.json()
    @staticmethod
    def count_collection(payload: Any) -> int:
        if isinstance(payload, list): return len(payload)
        if isinstance(payload, dict):
            for key in ("total", "totalCount", "count"):
                if isinstance(payload.get(key), int): return payload[key]
            for key in ("items", "data", "results"):
                if isinstance(payload.get(key), list): return len(payload[key])
        raise ValueError("Unsupported Plesk collection response format")
    def counts(self) -> dict[str,int]:
        return {
            "domains": self.count_collection(self.get_json("domains")),
            "clients": self.count_collection(self.get_json("clients")),
            "subscriptions": self.count_collection(self.get_json("subscriptions")),
        }

class PleskCollector:
    """Create fresh metrics on every Prometheus scrape."""
    def __init__(self, api: PleskAPI): self.api = api
    def collect(self):
        started = time.monotonic(); up = 1; counts = {}
        try: counts = self.api.counts()
        except (requests.RequestException, ValueError, TypeError) as exc:
            up = 0; print(f"Plesk scrape failed: {exc}", flush=True)
        yield GaugeMetricFamily("plesk_up", "Whether the last Plesk API scrape completed successfully.", value=up)
        if up:
            yield GaugeMetricFamily("plesk_domains_total", "Number of domains returned by the Plesk API.", value=counts["domains"])
            yield GaugeMetricFamily("plesk_clients_total", "Number of clients returned by the Plesk API.", value=counts["clients"])
            yield GaugeMetricFamily("plesk_subscriptions_total", "Number of subscriptions returned by the Plesk API.", value=counts["subscriptions"])
        yield GaugeMetricFamily("plesk_scrape_duration_seconds", "Time spent querying the Plesk API during the scrape.", value=time.monotonic()-started)

def main() -> None:
    config = Config.from_env(); REGISTRY.register(PleskCollector(PleskAPI(config)))
    port = int(os.getenv("PORT", "9784")); start_http_server(port)
    print(f"Plesk Prometheus exporter listening on :{port}", flush=True)
    while True: time.sleep(3600)

if __name__ == "__main__": main()
