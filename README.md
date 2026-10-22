# pagewatch

**Get notified when a web page, or just the part you care about, changes.**

pagewatch checks a list of pages on a schedule, compares them with the last snapshot, and sends you
the lines that were added or removed on Telegram or email. It runs entirely on **GitHub Actions**:
no server, no database, no cost. Every snapshot is committed to the repo, so git history is a
browsable archive of every version of every page.

```
pagewatch: 'react-native-releases' changed
https://reactnative.dev/releases/overview

+ 0.90.x | 2027-01-05 | 2027-02-09
+ 0.89.x | 2026-11-10 | 2026-12-07
- 0.89.x | 2026-11-03 | 2026-12-07
```

## Use cases

- Job openings on a company careers page, filtered by keywords
- Exam results, admit cards, and government notices that appear without warning
- Restocks, ticket sales, new rental listings
- Changes to API docs, SaaS pricing pages, terms of service, and privacy policies
- Course pages, club notice boards, and any site with no email alerts

## Quick start (about 5 minutes)

1. **Fork** this repo (or use it as a template).
2. Edit **`watches.yml`** to list the pages you want to watch.
3. Set up notifications by adding repository secrets (*Settings → Secrets and variables → Actions*):

   | Channel  | Secrets |
   |----------|---------|
   | Telegram | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
   | Email    | `SMTP_HOST`, `SMTP_PORT` (default 587), `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_TO`, optional `EMAIL_FROM` |

   Telegram: create a bot with [@BotFather](https://t.me/BotFather), send it a message, then open
   `https://api.telegram.org/bot<TOKEN>/getUpdates` to find your chat id.
4. Open the **Actions** tab, enable workflows, and run **pagewatch** once manually.
   The first run saves baselines, and later runs alert you on changes.

## Configuring watches

```yaml
watches:
  - id: acme-jobs                       # unique; also the snapshot file name
    url: https://acme.example/careers
    selector: "#open-positions"         # optional CSS selector, compares only this part of the page
    keywords: ["backend", "remote"]  # optional: alert only when an added line contains one of these
    ignore:                             # optional regexes stripped before comparing
      - "\\d+ views"
      - "(?i)updated .* ago"
    headers:                            # optional extra request headers
      Accept-Language: en-US
    enabled: true
```

**Avoiding false alerts:** narrow the page with `selector`, then strip anything that changes on every
load (timestamps, view counters, random tokens) with `ignore`. Use `preview` to see exactly what is
being compared.

## Running locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

python -m pagewatch list                 # show configured watches
python -m pagewatch preview react-native-releases   # print the extracted text (for tuning selectors)
python -m pagewatch run --dry-run        # check everything without saving or notifying
python -m pagewatch run --only google-play-announcements   # check a single watch
pytest                                   # run the tests
```

Notification secrets are read from environment variables, so you can export them locally to test alerts.

## How it works

```
watches.yml ─▶ fetch (httpx) ─▶ extract text (BeautifulSoup + selector + ignore rules)
                                        │
                     snapshots/<id>.txt ┴─▶ line diff ─▶ keyword filter ─▶ Telegram / email / console
                                        │
                     GitHub Actions commits the new snapshot ─▶ git history = full version archive
```

| Module | Responsibility |
|--------|----------------|
| `config.py`  | load and validate `watches.yml` |
| `fetch.py`   | HTTP fetching with sensible headers and timeouts |
| `extract.py` | HTML → normalized lines (drops scripts and styles, applies selector and ignore rules) |
| `diff.py`    | added and removed lines, keyword matching |
| `store.py`   | one plain-text snapshot per watch |
| `notify.py`  | console, Telegram and email channels, enabled by environment variables |
| `cli.py`     | `run`, `preview`, `list` |

## Security notes

- **Secrets stay in GitHub Secrets.** Notification credentials are read only from environment
  variables, and nothing sensitive is stored in the repo. GitHub also masks secret values in Actions logs.
- **Snapshots are public in a public repo.** Watch public pages only. Never put cookies, API keys or
  `Authorization` headers in `watches.yml`.
- **Pull requests from forks can't use your secrets.** The scheduled workflow only runs on a schedule or a
  manual trigger, and the CI workflow uses a read-only token.

## Limitations

- Pages rendered entirely by JavaScript may show little text, because pagewatch doesn't run a browser yet.
- GitHub may delay scheduled runs at busy times, so don't rely on minute-level precision.
- Please be polite: keep intervals reasonable and respect each site's terms.

## Roadmap

- [ ] Optional headless browser (Playwright) for JavaScript-heavy pages
- [ ] Discord and Slack webhooks
- [ ] Static GitHub Pages dashboard with change history
- [ ] Per-watch schedules
- [ ] Alert after N consecutive fetch errors

## License

MIT © Kushagra Sinha
