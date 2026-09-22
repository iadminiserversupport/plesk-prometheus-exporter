from unittest.mock import Mock
import pytest, requests
from plesk_exporter.exporter import Config, PleskAPI, PleskCollector

def test_config(monkeypatch):
    monkeypatch.setenv("PLESK_URL","https://plesk.example:8443"); monkeypatch.setenv("PLESK_API_KEY","secret")
    c=Config.from_env(); assert c.base_url.endswith(":8443") and c.api_key=="secret"

def test_count_shapes():
    assert PleskAPI.count_collection([1,2])==2
    assert PleskAPI.count_collection({"total":12,"items":[]})==12
    assert PleskAPI.count_collection({"items":[1]})==1
    with pytest.raises(ValueError): PleskAPI.count_collection({"unexpected":1})

def test_counts():
    s=Mock(); s.get.side_effect=[Mock(raise_for_status=Mock(),json=Mock(return_value=[1,2])),Mock(raise_for_status=Mock(),json=Mock(return_value={"total":3})),Mock(raise_for_status=Mock(),json=Mock(return_value={"items":[1]}))]
    assert PleskAPI(Config("https://p", "k"),s).counts()=={"domains":2,"clients":3,"subscriptions":1}

def metric_values(api):
    return {x.name:x.value for f in PleskCollector(api).collect() for x in f.samples}

def test_collector_success():
    a=Mock(); a.counts.return_value={"domains":10,"clients":4,"subscriptions":7}; v=metric_values(a)
    assert v["plesk_up"]==1 and v["plesk_domains_total"]==10 and v["plesk_clients_total"]==4 and v["plesk_subscriptions_total"]==7

def test_collector_failure():
    a=Mock(); a.counts.side_effect=requests.RequestException("failed"); v=metric_values(a)
    assert v["plesk_up"]==0 and "plesk_domains_total" not in v
