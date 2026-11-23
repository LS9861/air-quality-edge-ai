# Recording Log

Keep this updated **for every recording**. Future-you will not remember which
file was which scene, room, or condition — this is the ground truth behind the
labels. Copy the per-recording block for each session.

## Scene protocol (keep conditions consistent per class)

| Class      | Scene                                   | What to do |
|------------|-----------------------------------------|------------|
| `good`     | Window open / fresh outdoor air         | Open the window fully; keep it open for the whole run. No cooking, no candle, no traffic/smoke sources nearby. |
| `moderate` | Window closed / stuffy indoor air       | Close the window. Room occupied normally. No pollution source. This is the "stale air" case. |
| `poor`     | Candle smoke / elevated pollutants      | Light a candle (or incense) in the room, window closed. Keep the source active and (roughly) constant for the run. Ventilate afterwards. |

**Rules for trustworthy labels**
- One scene per recording — do not mix (e.g. don't light a candle mid-GOOD run).
- Keep the run **≥ 1 h** (longer = better; sliding windows need enough data).
- Record the same class at **different times of day** over multiple sessions
  (temperature/humidity/pollution drift → more robust model).
- Aim for roughly **balanced total time per class** (~5–7 h each to start).
- **Don't stop the recording early** just because readings look "boring" —
  steady data is exactly what the model needs.

## Recording template (copy this block per session)

```
### <YYYY-MM-DD HH:MM>  —  <good|moderate|poor>
- File:            air_quality_<scene>_<timestamp>.csv
- Duration:        __ min
- Time of day:     morning / afternoon / evening / night
- Room:            e.g. living room
- Conditions:      window open / closed / candle lit
- Occupancy:       people at home? (yes/no, how many)
- Outdoor weather: e.g. 4C, Cloudy (from OLED 'Out:' line)
- Indoor start:    Temp __.__C, Hum __%
- Indoor end:      Temp __.__C, Hum __%
- Notable:         anything unusual (traffic, cooking, cleaning, fan, etc.)
- Notes:           free text
```

---

## Sessions

<!-- Add your recordings below, newest last. -->

```
### <example> 2026-01-01 09:00 — good
- File:            air_quality_good_20260101_090000.csv
- Duration:        120 min
- Time of day:     morning
- Room:            living room
- Conditions:      window open
- Occupancy:       yes, 2
- Outdoor weather: 4C, Clear
- Indoor start:    21.8C, 55%
- Indoor end:      22.4C, 52%
- Notable:         light traffic outside around 08:30
- Notes:           first session, sensor after 30h burn-in
```
