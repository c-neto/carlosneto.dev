# My Blog!

This is my website, built with Sphinx!

URL: https://www.carlosneto.dev/

## Developer Notes

The content were created using [Sphinx](https://www.sphinx-doc.org/pt_BR/master/).

To install create a virtual environment and install dependencies, execute:

```bash
make setup
```

Setup the local web server to run a hot reload enironment:

```bash
make live
```

## Analytics (GoatCounter)

The [/analytics](https://carlosneto.dev/analytics/) page shows public stats for the site: visitors, countries, top posts, referrers, browsers, systems and screen sizes. The data comes from [GoatCounter](https://www.goatcounter.com), which uses no cookies and does not store IPs.

### How it works

```
visitor's browser ──(count.js)──▶ c-neto.goatcounter.com      collects each visit
                                          │
analytics.yml (hourly) ──(API + token)───┘
   scripts/goatcounter_export.py ──▶ analytics.json           aggregated stats
   git commit ──▶ gh-pages ──▶ carlosneto.dev/_static/analytics.json
                                          │
/analytics page (_static/analytics.js) ◀──┘                  renders charts and lists
```

1. **Collection.** `_templates/layout.html` loads GoatCounter's `count.js` on every page. On each page view it sends the path, title, referrer and screen size to `c-neto.goatcounter.com`. GoatCounter derives the country and browser from the request, then discards the IP. Visits from `localhost` are ignored, so `make live` does not count.
2. **Export.** `.github/workflows/analytics.yml` runs every hour. It calls `scripts/goatcounter_export.py`, which reads the GoatCounter API (`/api/v0/stats/...`) for the last 30 days and the last 12 months, and commits only `_static/analytics.json` to the `gh-pages` branch. The site is not rebuilt.
   Because the site deploy (`.github/workflows/deploy.yml`) replaces the whole `gh-pages` branch, it first downloads the published `analytics.json` and builds it back into the site. Both workflows share the `gh-pages-publish` concurrency group, so they never push at the same time.
3. **Render.** `analytics.md` holds the page markup. `_static/analytics.js` reads the JSON and draws the chart and lists, and `_static/analytics.css` styles them with the theme's colors, so light and dark mode work.

`_static/analytics.json` is git-ignored on `main`. It only exists on the `gh-pages` branch. GoatCounter itself keeps the raw data: use its dashboard, or export a CSV from **Settings → Export**.

### Setup

1. In GoatCounter, go to **Settings → API** and create a key with the **Read statistics** permission.
2. In GitHub, add it as the repository secret `GOATCOUNTER_TOKEN` (**Settings → Secrets and variables → Actions**).

Without the token, or if the API fails, the analytics workflow logs a warning and commits nothing, so the last published data stays online. Before the first successful run, the page shows "No data yet".

### Run locally

```bash
read -s GOATCOUNTER_TOKEN && export GOATCOUNTER_TOKEN
python3 scripts/goatcounter_export.py
make live
```

### Notes

- The numbers on the page are up to about an hour old. Run the **Update Analytics** workflow manually to refresh them sooner.
- GitHub disables scheduled workflows after 60 days without repository activity. If the page stops updating, re-enable the workflow in the Actions tab.
- Visitors with ad blockers are not counted, so the numbers are a lower bound.

---

> _Inspired in [choldgraf/choldgraf.github.io](https://github.com/choldgraf/choldgraf.github.io) created by [@choldgraf](https://github.com/choldgraf)!_
