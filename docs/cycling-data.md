# Cycling data from Apple Health

The cycling page used to pull rides from the Strava API. Strava made its API paid in June 2026
(an active subscription for every developer), and the daily workflow has failed with 403 Forbidden
since then. Rides now come from Apple Health ([D-018](DECISIONS.md#d-018-cycling-data-comes-from-apple-health-not-the-strava-api)).

Rides through June 21, 2026 stay in a frozen Strava archive (`_data/cycling_strava_archive.json`).
Strava missed many rides in 2026 (all of May, most of June), so Health rides on archive-era days
with no Strava ride are added too ([D-021](DECISIONS.md#d-021-health-fills-the-days-the-strava-archive-missed)).
Those and all newer rides go in `_data/cycling_rides.json`, and `scripts/cycling_data.py` rebuilds the page data
(`cycling_stats.json`, `cycling_calendar.json`) from both. There are two ways to add rides; use
both.

- **The Shortcut (automatic).** When an Apple Watch cycling workout ends, an iPhone Shortcut sends
  the ride's start, end, and distance to GitHub, and the site updates within a few minutes.
  Shortcuts can't read a workout's elevation, so these rides add no climbing.
- **The Health export (manual, every month or two).** Gives full detail, including elevation, for
  every ride, and fills in any the Shortcut missed. Rides the Shortcut already added are matched and
  updated, not duplicated.

## Manual: import an Apple Health export

1. On the iPhone, open **Health**, tap your picture (top right), then **Export All Health Data**,
   then **Export**. It takes a minute or two and makes `export.zip`.
2. AirDrop it to your computer or save it to Files.
3. In the repo, preview, then import:

   ```bash
   python3 scripts/cycling_data.py import-health ~/Downloads/export.zip --dry-run
   python3 scripts/cycling_data.py import-health ~/Downloads/export.zip
   ```

4. Commit the three `_data/cycling_*.json` files and push (or open a PR).

The export holds all of your health data. Never commit it: `export.zip`, `export.xml`, and
`apple_health_export/` are in `.gitignore`. Only cycling workouts after June 21, 2026, or on earlier
days with no Strava ride, are read. For each, only the date, morning or afternoon, distance,
moving time, and elevation are stored. No start times or routes are committed.

## Automatic: the ride Shortcut

### 1. Make a GitHub token for the Shortcut

1. Go to github.com → **Settings** → **Developer settings** → **Personal access tokens** →
   **Fine-grained tokens** → **Generate new token**.
2. Name it "ride shortcut", set an expiration (a year is fine; put a reminder in your calendar).
3. **Repository access:** Only select repositories → `joshchiou/joshchiou.github.io`.
4. **Permissions:** Repository permissions → **Contents: Read and write**. Nothing else.
5. Generate it and copy it. It goes only into the Shortcut, never into a chat, a file, or the repo.

The token can push to this repository and nothing else. If the phone is lost, delete the token on
the same page.

### 2. Build the automation

In the **Shortcuts** app on the iPhone paired with the Watch:

1. **Automation** tab → **+** → **Apple Watch Workout**. Set **When** to **Ends** and **Workout
   Type** to **Cycling** (add Indoor Cycling too if you want trainer rides counted). Choose **Run
   Immediately**, then **Next** → **Create New Shortcut**.
2. Add these actions in order:

   | #   | Action                       | Settings                                                                                                                    |
   | --- | ---------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
   | 1   | Find Health Samples          | Type **Workouts**; Sort by **Start Date**, Order **Latest First**, Limit **1**                                              |
   | 2   | Get Details of Health Sample | **Start Date** of the result of 1. Long-press the output, rename it **RideStart**                                           |
   | 3   | Get Details of Health Sample | **End Date** of the result of 1. Rename it **RideEnd**                                                                      |
   | 4   | Find Health Samples          | Type **Cycling Distance**; filters: **Start Date** is after **RideStart**, and **End Date** is before **RideEnd**; no limit |
   | 5   | Get Details of Health Sample | **Value** of the result of 4                                                                                                |
   | 6   | Calculate Statistics         | **Sum** of the result of 5. Rename it **Miles**                                                                             |
   | 7   | Format Date                  | **RideStart**, Date Format **ISO 8601**, Include ISO 8601 Time **on**. Rename it **StartISO**                               |
   | 8   | Format Date                  | **RideEnd**, same settings. Rename it **EndISO**                                                                            |
   | 9   | Get Contents of URL          | URL `https://api.github.com/repos/joshchiou/joshchiou.github.io/dispatches`; see below                                      |

   For action 9, tap **Show More** and set:
   - **Method:** POST
   - **Headers:** `Authorization` = `Bearer ` followed by the token; `Accept` =
     `application/vnd.github+json`
   - **Request Body:** JSON, with a Text field `event_type` = `ride`, and a Dictionary field
     `client_payload` containing Text `start` = **StartISO**, Text `end` = **EndISO**, Number
     `distance` = **Miles**, Text `unit` = `mi`

   If Health shows your distances in kilometers, set `unit` to `km`.

3. Tap **Done**.

### 3. Test it

- Without riding: on github.com, **Actions** → **Add Ride** → **Run workflow**, and enter a
  start, end, distance, and unit by hand. That checks the GitHub side.
- With the Shortcut: after a short ride, open the Shortcut from the Automation tab and tap the run
  button, or just finish a real ride. A green **Add Ride** run on GitHub, then a **Deploy site**
  run, means it worked. The cycling page footer shows the last ride's date.

### Limits

- The trigger needs the workout to be recorded on the Apple Watch. Rides started on the iPhone
  alone don't fire it; the next Health export picks them up.
- The phone needs a connection when the workout ends. A failed post isn't retried; the export fills
  the gap.
- Shortcut action names move around between iOS versions. If one above is missing, search the
  action list for the closest match; the payload the workflow expects is what matters
  (`start` and `end` in ISO 8601 with a time zone, `distance`, `unit`).
- `check_site.py` warns when no ride has been logged for 45 days, which usually means the Shortcut
  stopped running (an expired token is the most likely cause).

## Alternatives considered

- **Paying Strava** ($11.99/month for API access) would revive the old workflow unchanged.
- **Health Auto Export** (a paid iPhone app) can post workouts with elevation automatically, but
  it sends its own JSON format, which GitHub's API won't accept without a relay server in between.
- Apple has no web API for Health data, so a scheduled GitHub workflow can't fetch rides on its
  own; the phone has to send them.
