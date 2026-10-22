# pagewatch

**Get a Telegram message when a web page, or just the part you care about, changes.**

pagewatch checks a list of pages on a schedule, compares each one with its last snapshot, and sends
you the lines that were added or removed. It runs entirely on **GitHub Actions**: no server, no
database, no cost for public repos. Every snapshot is committed to the repo, so git history is a
browsable archive of every version of every page.

```
pagewatch: 'react-native-releases' changed
https://reactnative.dev/releases/overview

+ 0.90.x | 2027-01-05 | 2027-02-09
+ 0.89.x | 2026-11-10 | 2026-12-07
- 0.89.x | 2026-11-03 | 2026-12-07
```

`+` lines are new, `-` lines were removed. A `-`/`+` pair for the same item means it changed:
above, a new version 0.90.x was added and the 0.89.x branch cut moved from Nov 3 to Nov 10.

## What this repo watches

| Watch | Page | Alerts when |
|-------|------|-------------|
| `react-native-releases` | [React Native release schedule](https://reactnative.dev/releases/overview) | a new version is added, or a branch cut or release date changes |
| `google-play-announcements` | [Play Console policy announcements](https://support.google.com/googleplay/android-developer/announcements/13412212) | a new announcement is published |

Checks run **every 5 days** (see [Schedule](#schedule)). Fork the repo and edit `watches.yml` to
watch your own pages.

## Other use cases

- Job openings on a company careers page, filtered by keywords
- Exam results, admit cards and government notices that appear without warning
- Restocks, ticket sales and new rental listings
- Changes to API docs, SaaS pricing pages, terms of service and privacy policies
- Course pages, club notice boards, and any site with no email alerts

## Quick start (about 10 minutes)

1. **Fork** this repo, or use it as a template. Keep it **public**: GitHub Actions is free for
   public repos.
2. Edit **`watches.yml`** to list the pages you want to watch (see [Configuring watches](#configuring-watches)).
3. **Set up Telegram alerts**, following the steps below.
4. Open the **Actions** tab, enable workflows if asked, then choose **pagewatch → Run workflow**.
   The first run only saves baselines to `snapshots/` and sends no message. Later runs alert you
   when something changes.
5. Optionally, [send yourself a test alert](#testing-an-alert).

## Telegram setup

Telegram bots are free. You need two values: a **bot token** and your **chat ID**.

### 1. Create a bot

1. In Telegram, open [@BotFather](https://t.me/BotFather) (it has a blue verified tick).
2. Send `/newbot`.
3. Choose a display name (e.g. `Pagewatch`) and a username ending in `bot`
   (e.g. `yourname_pagewatch_bot`).
4. BotFather replies with a token like `8123456789:AAH...`. **Treat it like a password**: never
   commit it, paste it into an issue, or show it in a screenshot.

### 2. Get your chat ID

1. Open your new bot in Telegram and press **Start**, or send it any message.
   A bot can't message you until you have done this.
2. In a browser, open the URL below, replacing `<TOKEN>` with your token:
   ```
   https://api.telegram.org/bot<TOKEN>/getUpdates
   ```
3. Find `"chat":{"id":123456789` in the response. That number is your **chat ID**.
   If you see `"result":[]`, send the bot another message and refresh.

### 3. Test the bot (optional, but recommended)

```bash
curl -s "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d chat_id=<CHAT_ID> -d text="pagewatch test ✅"
```

You should receive the message straight away. This command saves your token in your shell history,
so remove it afterwards (on macOS with zsh):

```bash
sed -i '' '/api.telegram.org\/bot/d' ~/.zsh_history
```

### 4. Add the secrets to GitHub

With the [GitHub CLI](https://cli.github.com/), run these in the repo folder. Each one prompts for the
value, so it never ends up in your shell history:

```bash
gh secret set TELEGRAM_BOT_TOKEN
gh secret set TELEGRAM_CHAT_ID
```

Or add them on GitHub under **Settings → Secrets and variables → Actions → New repository secret**.

Secrets are encrypted, can't be viewed again (only replaced), are masked as `***` in Actions logs,
and aren't available to pull requests from forks.

**If your token ever leaks:** send `/revoke` to @BotFather, pick your bot, and save the new token
with `gh secret set TELEGRAM_BOT_TOKEN`. The old token stops working immediately.

### Email instead of, or as well as, Telegram

Add these secrets: `SMTP_HOST`, `SMTP_PORT` (default 587), `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_TO`,
and optionally `EMAIL_FROM`. For Gmail, use an [app password](https://support.google.com/accounts/answer/185833),
not your normal password. Every channel whose secrets are set is used.

## Testing an alert

The first run for a watch saves a baseline and sends nothing. To see a real alert:

1. On GitHub, open a snapshot such as `snapshots/google-play-announcements.txt`.
2. Click the ✏️ **edit** icon, delete **one line**, and commit.
   Don't delete the whole file: with no snapshot, the next run treats it as a first run and
   only saves a new baseline.
3. Run the workflow from the Actions tab. You should get a Telegram message showing that line as a
   `+` addition, and the snapshot is restored automatically.

## Schedule

The schedule is set in `.github/workflows/pagewatch.yml`:

```yaml
- cron: "17 3 */5 * *"   # 03:17 UTC (08:47 IST) on days 1, 6, 11, 16, 21, 26 and 31
```

- **Cron times are in UTC.**
- **The 5-day cycle restarts on the 1st of each month**, so there's a 1-day gap after the 31st, a
  3–4 day gap after February, and exactly 5 days otherwise. You're never left more than 5 days
  without a check.
- **The start time is set off the hour** because GitHub's busiest time is on the hour, when
  scheduled runs are more likely to be delayed. Runs can still start a few minutes late.
- **You can run it any time** with **Actions → pagewatch → Run workflow**.

| Schedule | Cron |
|----------|------|
| Every 30 minutes | `*/30 * * * *` |
| Hourly | `17 * * * *` |
| Daily at 08:47 IST | `17 3 * * *` |
| Every 5 days | `17 3 */5 * *` |
| Every Monday | `17 3 * * 1` |

**GitHub's 60-day rule:** in public repos, GitHub disables scheduled workflows after 60 days with no
repository activity. The bot only commits when a page changes, so a quiet period can trigger this.
GitHub emails you a warning first, and you can re-enable the workflow with one click in the Actions tab.

## Configuring watches

```yaml
watches:
  - id: acme-jobs                       # unique; also the snapshot file name
    url: https://acme.example/careers
    selector: "#open-positions"         # optional CSS selector: compare only this part of the page
    keywords: ["backend", "remote"]     # optional: alert only if an ADDED line contains one of these
    ignore:                             # optional regexes removed from each line before comparing
      - "\\d+ views"
      - "(?i)updated .* ago"
    headers:                            # optional extra request headers
      Accept-Language: en-US
    enabled: true                       # set to false to pause a watch
```

- **Tables:** each table row becomes one line, `cell | cell | cell`, so a changed row shows up as one
  readable line. To ignore trailing columns, add an `ignore` regex that strips them. The React Native
  watch does this to ignore the Support and Blog post columns.
- **Avoiding false alerts:** narrow the page with `selector`, then use `ignore` to strip anything
  that changes on every load (timestamps, view counters, random tokens).
- **Finding a selector:** in your browser, right-click the content → **Inspect**, and look for a
  class or id on a wrapping element. Then check it with `python -m pagewatch preview <id>`.
- **URLs:** remove tracking parameters such as `sjid=` or `utm_*`. For Google pages, add `hl=en` so
  GitHub's US-based servers always get the English version.

## Running locally

Requires **Python 3.10+**. On macOS the built-in `python3` is 3.9, so install a newer one first,
e.g. `brew install python@3.12`.

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

python -m pagewatch list                                  # show configured watches
python -m pagewatch preview react-native-releases         # print the extracted text (for tuning selectors)
python -m pagewatch run --dry-run                         # check everything without saving or notifying
python -m pagewatch run --only google-play-announcements  # check a single watch
pytest && ruff check .                                    # tests and lint
deactivate                                                # leave the virtual environment
```

Notification secrets are read from environment variables, so you can `export TELEGRAM_BOT_TOKEN=...`
and `export TELEGRAM_CHAT_ID=...` to test alerts locally.

### Pushing changes

The bot commits snapshot updates to `main`, so GitHub often has commits you don't have locally.
Pull with rebase before pushing:

```bash
git pull --rebase
git push
```

Run `git config --global pull.rebase true` once to make plain `git pull` do this automatically.

## Troubleshooting

| Symptom | Cause and fix |
|---------|---------------|
| Workflow ran but no Telegram message | It was a first run (baseline), or nothing changed. Check the run log for `[baseline]`, `[unchanged]` or `[changed]`. |
| `Telegram API request failed (HTTP 401)` | Wrong bot token. Update the `TELEGRAM_BOT_TOKEN` secret. |
| `Telegram API request failed (HTTP 400)` | Wrong chat ID, or you haven't pressed **Start** on your bot. |
| `selector '...' matched nothing` | The page layout changed or the selector is wrong. Inspect the page and test with `preview`. |
| Scheduled runs stopped | GitHub's 60-day inactivity rule. Re-enable the workflow in the Actions tab. |
| `git push` rejected (fetch first) | The bot pushed snapshots. Run `git pull --rebase`, then push. |

## How it works

```
watches.yml ─▶ fetch (httpx) ─▶ extract text (BeautifulSoup + lxml, selector, ignore rules)
                                        │
                     snapshots/<id>.txt ┴─▶ line diff ─▶ keyword filter ─▶ Telegram / email / console
                                        │
                     GitHub Actions commits the new snapshot ─▶ git history = full version archive
```

| Module | Responsibility |
|--------|----------------|
| `config.py`  | load and validate `watches.yml` |
| `fetch.py`   | HTTP fetching with sensible headers and timeouts |
| `extract.py` | HTML → normalized lines: parses like a browser (lxml), drops scripts and styles, applies selector and ignore rules, one line per table row |
| `diff.py`    | added and removed lines, keyword matching |
| `store.py`   | one plain-text snapshot per watch |
| `notify.py`  | console, Telegram and email channels, enabled by environment variables |
| `cli.py`     | `run`, `preview`, `list` |

## Security notes

- **Secrets stay in GitHub Secrets.** Credentials are read only from environment variables, never
  written to files or snapshots, and the bot token is never included in error messages.
- **Everything in a public repo is public**, including `watches.yml` and every snapshot. Watch public
  pages only, and never put cookies, API keys or `Authorization` headers in the config.
- **Fork pull requests can't reach your secrets.** The scheduled workflow only runs on its schedule
  or when you start it manually, and CI uses a read-only token.
- **Keep your email private in commits.** Turn on *Keep my email addresses private* and *Block
  command line pushes that expose my email* in GitHub's email settings, and commit with your
  `…@users.noreply.github.com` address.

## Limitations

- Pages rendered entirely by JavaScript may show little text, because pagewatch doesn't run a browser yet.
- GitHub may delay or occasionally skip scheduled runs at busy times.
- Please be polite: keep intervals reasonable and respect each site's terms.

## Roadmap

- [ ] Optional headless browser (Playwright) for JavaScript-heavy pages
- [ ] Discord and Slack webhooks
- [ ] Static GitHub Pages dashboard with change history
- [ ] Per-watch schedules
- [ ] Alert after N consecutive fetch errors
- [ ] Keep-alive so the 60-day rule never pauses the schedule

## License

MIT © Kushagra Sinha
