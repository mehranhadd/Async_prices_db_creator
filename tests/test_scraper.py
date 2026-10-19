from __future__ import annotations

import pytest

from async_prices_db_creator import scraper
from async_prices_db_creator.config import get_database_path


def test_category_link_uses_exact_original_anchor_string():
    html = '''
    <html><body>
      <a href="/mobiles">قیمت گوشی</a>
      <a href="/other"><span>قیمت گوشی</span></a>
    </body></html>
    '''
    assert scraper.find_category_url_from_html(html, "https://example.test") == (
        "https://example.test/mobiles"
    )


def test_category_link_accepts_absolute_href():
    html = '<a href="https://store.example/mobiles">قیمت گوشی</a>'
    assert scraper.find_category_url_from_html(html, "https://example.test") == (
        "https://store.example/mobiles"
    )


def test_category_link_missing_raises_clear_error():
    with pytest.raises(LookupError, match="Could not find a link"):
        scraper.find_category_url_from_html("<html><a href='/other'>Other</a></html>")


def test_product_extraction_preserves_original_first_class_rule():
    html = '''
    <html><body>
      <a class="line-clamp-3 other">Phone A\tplus</a>
      <a class="other line-clamp-3">Should not be selected</a>
      <p class="text-[22px] text-bold">123</p>
      <p class="text-bold text-[22px]">Should not be selected</p>
    </body></html>
    '''
    names, prices = scraper.parse_product_html(html)
    assert names == ["Phone A\tplus"]
    assert prices == ["123"]


def test_collect_products_removes_tabs_and_pairs_in_list_order(monkeypatch):
    homepage = '<a href="/mobiles">قیمت گوشی</a>'
    listing = '''
    <a class="line-clamp-3">Phone\tOne</a><a class="line-clamp-3">Phone Two</a>
    <p class="text-[22px]">100</p><p class="text-[22px]">200</p>
    '''
    requested = []

    def fake_get_html(url, timeout):
        requested.append((url, timeout))
        return homepage if url == "https://example.test" else listing

    monkeypatch.setattr(scraper, "get_html_sync", fake_get_html)
    products = scraper.collect_products("https://example.test", timeout=2.5)
    assert products == [("PhoneOne", "100"), ("Phone Two", "200")]
    assert requested == [
        ("https://example.test", 2.5),
        ("https://example.test/mobiles", 2.5),
    ]


def test_database_path_defaults_inside_project():
    path = get_database_path()
    assert path.is_absolute()
    assert path.name == "Phone_prices.db"
    assert path.parent.name == "data"


def test_database_path_expands_tilde(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    path = get_database_path("~/phone-prices.db")
    assert path == tmp_path / "phone-prices.db"


def test_category_link_does_not_fuzzy_match_text():
    html = '<a href="/mobiles">سایت قیمت گوشی موبایل</a>'
    with pytest.raises(LookupError):
        scraper.find_category_url_from_html(html, "https://example.test")


def test_get_html_sync_passes_timeout_and_raises_http_errors(monkeypatch):
    class FakeResponse:
        text = "<html>ok</html>"

        def raise_for_status(self):
            return None

    seen = {}

    def fake_get(url, *, headers, timeout):
        seen.update(url=url, headers=headers, timeout=timeout)
        return FakeResponse()

    monkeypatch.setattr(scraper.requests, "get", fake_get)
    assert scraper.get_html_sync("https://example.test", timeout=3) == "<html>ok</html>"
    assert seen["url"] == "https://example.test"
    assert seen["timeout"] == 3


def test_get_html_sync_propagates_http_error(monkeypatch):
    import requests

    class FakeResponse:
        text = ""

        def raise_for_status(self):
            raise requests.HTTPError("404 Not Found")

    monkeypatch.setattr(scraper.requests, "get", lambda *args, **kwargs: FakeResponse())
    with pytest.raises(requests.HTTPError, match="404 Not Found"):
        scraper.get_html_sync("https://example.test")
