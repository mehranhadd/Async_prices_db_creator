# Async Prices DB Creator

An asynchronous Python exercise that collects product names and prices from the **Mobile Phones** category on [Technolife](https://technolife.ir/) and saves them to SQLite using `aiosqlite`.

> **Website compatibility:** Retail websites can change their markup, so a live run may need selector updates after inspecting the current HTML. This project does not include a live-site integration test.

## Requirements

- Python 3.10 or newer
- Network access to the target website
- The website's current HTML must still match the selectors in `scraper.py`

## Install

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows PowerShell instead:
# .venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

To install runtime dependencies without installing the project as a package:

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
phone-prices-db
```

The original script filename remains available as a launcher:

```bash
python Prices_db_creator.py
```

By default, the database is created at `data/Phone_prices.db` inside the project directory. The existing database schema is preserved:

```sql
CREATE TABLE IF NOT EXISTS mobiles (
    name TEXT PRIMARY KEY,
    price TEXT
)
```

The default run prints the rows in the database after insertion. To suppress the listing:

```bash
phone-prices-db --no-print-rows
```

### Configuration

| Setting | Purpose | Default |
|---|---|---|
| `TECHNOLIFE_BASE_URL` | Homepage URL | `http://technolife.ir` |
| `PHONE_PRICES_DB` | Database path override | `<project>/data/Phone_prices.db` |
| `HTTP_TIMEOUT_SECONDS` | Default HTTP timeout | `20` seconds |
| `HTTP_USER_AGENT` | Optional custom User-Agent header | Unset; Requests uses its defaults |

You can also override values for one run:

```bash
phone-prices-db --home-url "https://technolife.ir" --timeout 30 --database "data/Phone_prices.db"
```

Relative database paths are resolved from the project root; `~` is expanded. Parent directories are created automatically. Explicit command-line database paths take precedence over `PHONE_PRICES_DB`.

## How it works

1. Fetch the homepage with `requests` and locate the category link whose anchor string is exactly `قیمت گوشی`.
2. Fetch that category page.
3. Collect product names from anchors whose **first class** is `line-clamp-3` and prices from paragraphs whose **first class** is `text-[22px]`.
4. Remove tab characters from names and pair names and prices in list order using `zip`.
5. Initialize the SQLite database and `mobiles` table, then insert the products.
6. Print existing table rows unless `--no-print-rows` is passed.

The two separate lists are paired using `zip`, so if the site returns different counts of name and price elements, unmatched trailing values are not saved.

The CLI explicitly initializes the SQLite database and schema after scraping succeeds and before insertion. Database insertion uses one `aiosqlite` connection per run and commits each row as the original code did. The schema and plain `INSERT` behavior are unchanged; because `name` is a primary key, attempting to insert an already-present name raises an SQLite integrity error rather than silently overwriting it. If using `save_products()` directly from Python, call `initialize_database()` first.

## Tests

The test suite uses saved, synthetic HTML snippets and a temporary SQLite database; it does not contact Technolife or change your real database.

```bash
pytest
```

## Limitations

- The scraper is sensitive to website markup changes.
- It does not infer which name and price belong to the same product card; it preserves the original document-order pairing.
- Product name is the table primary key, so repeated names cannot be inserted twice.
- Prices are stored as `TEXT`, rather than normalizing prices to numeric values.