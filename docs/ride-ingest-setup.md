# Automatic ride ingest from Apple Health

Apple Health has no cloud API — nothing can pull from it, so the phone has to
push. This sets up a Shortcut that posts finished rides to the repo, which then
rebuilds the cycling page on its own.

Everything on the server side is already built and tested. What follows is the
phone side, which needs doing by hand once.

## 1. Create a token

GitHub → Settings → Developer settings → **Fine-grained personal access tokens**
→ Generate new token.

- **Repository access:** Only select repositories → `joshchiou.github.io`
- **Permissions:** Repository permissions → **Contents: Read and write**
  (that is the only one needed; `repository_dispatch` is a contents write)
- **Expiration:** set one. A year is reasonable; the Shortcut will start failing
  when it lapses, which is the reminder to rotate it.

Copy the token. It goes on your phone, so keep it narrow — this is why it is a
fine-grained token scoped to one repo rather than a classic token.

## 2. Build the Shortcut

Shortcuts app → new shortcut, named e.g. "Post ride".

1. **Find Health Samples** — Cycling Distance, where Start Date is in the last
   1 day. (If you have _Health Exporter & Shortcuts_ installed, use its
   **Export Workouts** action instead: it returns full workout JSON including
   elevation, which plain Shortcuts cannot reach.)
2. **Calculate Statistics** — Sum, to total the distance for the ride.
3. **Text** — build the payload. With a `Distance` variable in kilometres and a
   `Start` date formatted `yyyy-MM-dd'T'HH:mm:ss`:

   ```json
   {
     "event_type": "new-rides",
     "client_payload": {
       "rides": [{ "start": "Start", "distance_km": Distance }]
     }
   }
   ```

   Replace `Start` and `Distance` with the Shortcuts variables. Single-digit
   hours are fine — the parser accepts them.

4. **Get Contents of URL**
   - URL: `https://api.github.com/repos/joshchiou/joshchiou.github.io/dispatches`
   - Method: **POST**
   - Headers:
     - `Authorization`: `Bearer <your token>`
     - `Accept`: `application/vnd.github+json`
   - Request Body: **File** → the Text from step 3

A successful dispatch returns **204 No Content** with an empty body. An empty
response is success, not failure.

## 3. Automate it

Shortcuts → Automation → New.

- **Best trigger:** _Apple Watch Workout_ → Cycling → **When: Ends**. Fires once
  per ride, right when it finishes.
- **Alternative:** _Time of Day_, once each evening, with step 1 widened to the
  whole day. Simpler, but it lumps a two-way commute into one entry.

Turn **Ask Before Running** off so it fires unattended.

## 4. Check it

Ride, or run the Shortcut by hand. Then look at Actions → **Ingest Rides**. It
will merge the ride, rebuild the derived data, and commit.

Reposting the same ride is harmless — rides are deduplicated on start time
(±25 min) and distance (±25%), so a Shortcut that fires twice, or a retry after
a failure, cannot double-count. Two commutes on the same day stay separate
because the match is on start time, not date.

## Payload shapes

The canonical shape, the one to build above:

```json
{
  "rides": [
    {
      "start": "2026-07-26T08:10:00",
      "distance_km": 14.5,
      "elevation_m": 120,
      "duration_min": 45,
      "indoor": false
    }
  ]
}
```

Only `start` and `distance_km` are required. Also accepted, so the phone-side
app can be swapped without touching the server:

- a bare top-level array of rides
- `{"workouts": [...]}` and Health Auto Export's `{"data": {"workouts": [...]}}`
- measurements as `{"qty": 9.0, "units": "mi"}` as well as plain numbers
- miles/kilometres/metres, feet/metres/centimetres, seconds/minutes/hours
- field aliases: `startDate`, `distance`, `elevationUp`, `duration`, …

Anything that isn't cycling, is under 1 km, or has no usable start or distance
is skipped and reported, never guessed at.

## Testing without a phone

```bash
export RIDES_PAYLOAD='{"rides":[{"start":"2026-07-26T08:10:00","distance_km":14.5}]}'
python3 scripts/ingest_rides.py --payload-env RIDES_PAYLOAD --dry-run
```

## If it stops working

The workflow opens a single tracking issue on failure. Common causes:

- **403 from GitHub** — token expired, or it lacks Contents: write.
- **"contained no workouts"** — the Shortcut's JSON shape drifted; compare it
  against the canonical shape above.
- **Nothing happens at all** — check the automation has _Ask Before Running_
  off, and that the Shortcut runs correctly when triggered manually.

## Relationship to the bulk export

This keeps the site current day to day. The full export
(`scripts/parse_apple_health.py`) remains the way to backfill history or repair
gaps, and the two compose: both write the same record shape into
`_data/health_rides.json`, and the same deduplication applies to both.
