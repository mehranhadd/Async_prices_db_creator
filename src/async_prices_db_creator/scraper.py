"""HTTP and HTML extraction for the Technolife mobile-phone listing.

The HTML-selection rules below are based on the author's manual inspection
of the site and should only be changed after checking representative HTML.
"""

from __future__ import annotations

from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from .config import (
    BASE_URL,
    CATEGORY_LINK_TEXT,
    REQUEST_TIMEOUT_SECONDS,
    request_headers,
)


def get_html_sync(url: str, timeout: float = REQUEST_TIMEOUT_SECONDS) -> str:
    """Fetch HTML synchronously and raise a useful error for HTTP failures."""
    response = requests.get(url, headers=request_headers(), timeout=timeout)
    response.raise_for_status()
    return response.text


def find_category_url_from_html(html: str, base_url: str = BASE_URL) -> str:
    """Find the mobile-phone category using the original exact anchor text.

    Deliberately uses ``link.string == 'قیمت گوشی'`` rather than a broader
    ``get_text()`` search, to avoid silently changing the original selector.
    """
    dom = BeautifulSoup(html, "html.parser")
    for link in dom.find_all("a"):
        if link.string == CATEGORY_LINK_TEXT:
            href = link.get("href")
            if href:
                # urljoin handles both root-relative and absolute href values.
                return urljoin(base_url, href)
    raise LookupError(
        f"Could not find a link with the exact text {CATEGORY_LINK_TEXT!r}. "
        "The site markup may have changed."
    )


def find_category_url(
    url: str = BASE_URL, timeout: float = REQUEST_TIMEOUT_SECONDS
) -> str:
    """Fetch the homepage and return the mobile-phone category URL."""
    html = get_html_sync(url, timeout=timeout)
    return find_category_url_from_html(html, base_url=url)


def parse_product_html(html: str) -> tuple[list[str], list[str]]:
    """Extract product names and prices using the original class checks.

    Names are collected from anchors whose first class is ``line-clamp-3``;
    prices are collected from paragraphs whose first class is ``text-[22px]``.
    The lists remain separate.
    """
    dom = BeautifulSoup(html, "html.parser")
    names: list[str] = []
    prices: list[str] = []

    # Preserve the original selector: the first class value must match.
    for a_tag in dom.find_all("a"):
        classes = a_tag.get("class")
        if classes and len(classes) != 0 and classes[0] == "line-clamp-3":
            value = a_tag.string
            names.append(value)

    # Preserve the original selector and content extraction behavior.
    for p_tag in dom.find_all("p"):
        classes = p_tag.get("class")
        if classes and len(classes) != 0 and classes[0] == "text-[22px]":
            prices.append(p_tag.contents[0])

    return names, prices


def collect_products(
    home_url: str = BASE_URL, timeout: float = REQUEST_TIMEOUT_SECONDS
) -> list[tuple[str, str]]:
    """Fetch the category listing and pair extracted names with prices.

    Tabs are removed from product names, and names and prices are
    paired in document-order list order with ``zip``.
    """
    category_url = find_category_url(home_url, timeout=timeout)
    listing_html = get_html_sync(category_url, timeout=timeout)
    names, prices = parse_product_html(listing_html)

    cleaned_names = [name.replace("\t", "") for name in names]
    return list(zip(cleaned_names, prices))
