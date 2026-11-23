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

## Burn-in & maintenance
- Run the sensor **1–2 days continuously** once before recording (MQ-135 needs
  ~24–48 h total on-time for its baseline to stop drifting).
- **Short power-offs (≤ 1 h) are fine** — burn-in is cumulative, not reset.
- After **any** power-off, let it **warm up 15–30 min** before recording.
- Do **not** power off right before or during a recording session.

## Recording plan (2–3 days, back-to-back blocks)

Do **back-to-back blocks** (~1 h per scene, two scenes per block ≈ 2 h), and
**rotate the scene order each block** so no class is stuck at one time of day.
This finishes fast while still giving the model diverse conditions.
Target: roughly **4–6 h per class** across the plan.

| Day | Morning block (~2 h) | Afternoon block (~2 h) | Evening block (~2 h) |
|-----|----------------------|------------------------|----------------------|
| **1** | GOOD → MODERATE        | POOR → GOOD            | MODERATE → POOR      |
| **2** | POOR → MODERATE        | GOOD → POOR            | MODERATE → GOOD      |
| **3** | *optional top-up:* whichever class has the least total time | | |

**Per-block procedure**
1. Let the sensor warm up (15–30 min if it was off).
2. Run **scene 1 for ~60 min** → stop (Ctrl+C), note it in Sessions below.
3. **Setup scene 2** (open/close window, light candle, ventilate if leaving POOR).
4. Run **scene 2 for ~60 min** → stop, note it.
5. If moving away from POOR, **ventilate the room** before the next session.

*Fast alternative (if short on time):* do a single back-to-back GOOD → MODERATE
→ POOR day (~2 h each ≈ 6 h), then repeat on **one other day at a different
time of day**. That's ~4 h/class — enough for a first model.

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

### Progress tracker (update as you go)

| Class      | Target | Recorded so far | Status |
|------------|--------|-----------------|--------|
| `good`     | ~4–6 h | 0 h             | ☐ |
| `moderate` | ~4–6 h | 0 h             | ☐ |
| `poor`     | ~4–6 h | 0 h             | ☐ |

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
