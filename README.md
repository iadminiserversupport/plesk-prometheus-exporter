# Plesk Prometheus Exporter

A small Prometheus exporter exposing read-only Plesk REST API inventory metrics. It complements Node Exporter rather than duplicating Linux host metrics.

## Metrics

- `plesk_up` — whether the latest Plesk API scrape succeeded
- `plesk_domains_total` — domains returned by Plesk
- `plesk_clients_total` — clients returned by Plesk
- `plesk_subscriptions_total` — subscriptions returned by Plesk
- `plesk_scrape_duration_seconds` — time spent querying Plesk

The Python Prometheus client also exposes its normal process/runtime metrics.

## Requirements

- Plesk Obsidian with REST API support
- Python 3.9+
- A Plesk API key with sufficient read permissions
- Network access to Plesk TCP 8443
- Prometheus

Plesk documents the REST API at `https://<host>:8443/api/v2/` and recommends API keys over basic authentication.

## Configuration

```bash
export PLESK_URL="https://plesk.example.com:8443"
export PLESK_API_KEY="your-api-key"
export PLESK_VERIFY_SSL="true"
export PLESK_TIMEOUT="10"
export PORT="9784"
```

Keep TLS verification enabled in normal deployments.

## Run

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m plesk_exporter.exporter
```

Then:

```bash
curl http://127.0.0.1:9784/metrics
```

## Prometheus

```yaml
scrape_configs:
  - job_name: "plesk"
    static_configs:
      - targets: ["plesk-exporter.example.com:9784"]
```

## Docker

```bash
export PLESK_API_KEY="your-api-key"
docker compose up -d --build
```

Do not commit the API key. Use a secret-management system for production deployments.

## Plesk API calls

The exporter performs read-only GET requests to:

```text
/api/v2/domains
/api/v2/clients
/api/v2/subscriptions
```

If the API request fails or an unexpected response is returned, `plesk_up` becomes `0`; the exporter remains available for later scrapes.

## Testing

```bash
pip install -r requirements.txt
pytest -q
```

Tests mock the API and cover configuration, collection parsing, successful collection, and API failure handling.

## Security

Use HTTPS and certificate verification. Restrict the API key and network access according to the Plesk server's security policy.

## Cloud server administration

For cloud Linux environments requiring ongoing administration, troubleshooting, performance optimization, or hands-on server management, see [Cloud Server Management](https://iserversupport.com/cloud-server-management/).

## License

MIT
