# Architecture and refactor notes

## Modules

- `src/async_prices_db_creator/config.py`: defaults, environment overrides, and project-rooted database path resolution.
- `src/async_prices_db_creator/scraper.py`: synchronous HTTP and BeautifulSoup parsing. Kept separate from the asynchronous database layer.
- `src/async_prices_db_creator/database.py`: explicit SQLite schema initialization, insertion, and reading through `aiosqlite`. The CLI calls `initialize_database()` before saving rows.
- `src/async_prices_db_creator/cli.py`: command-line arguments and workflow orchestration.
- `Prices_db_creator.py`: compatibility launcher that retains the original script filename.
- `tests/`: offline unit tests.

## Extraction rules

The supplied script's HTML-matching logic:

1. Category links are matched by `link.string == "قیمت گوشی"`.
2. Product names are taken from `<a>` elements whose first class is `line-clamp-3`.
3. Prices are taken from `<p>` elements whose first class is `text-[22px]`.
4. Tabs are removed from names.
5. The separately collected lists are paired using `zip(names, prices)` in source order.

The refactor does not claim these selectors have been revalidated against current live HTML. Update them only after inspecting representative pages and adding fixtures/tests for the revised behavior.

## Intentional engineering changes

- The absolute, machine-specific database path was replaced with `<project root>/data/Phone_prices.db` by default. This makes the project portable; `PHONE_PRICES_DB` and `--database` can override it. Tilde and relative paths are handled explicitly.
- Missing parent directories are created recursively.
- HTTP requests have a timeout and `raise_for_status()` surfaces non-success HTTP responses rather than passing a missing HTML value to BeautifulSoup.
- If `HTTP_USER_AGENT` is configured, it is sent as a header. If absent, the empty User-Agent header from the original script is omitted and Requests supplies its defaults.
- Database operations reuse one asynchronous connection and preserve the existing schema, plain `INSERT`, and per-row commit semantics. This avoids opening a separate connection for every row while keeping earlier successful rows committed if a later insert fails.
- Live HTTP interaction is only performed when the application is explicitly run. Importing the package does not crawl the site.