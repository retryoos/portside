# Architecture — Live Exposure Detection ("Claims Radar") (Pick 2)

> Production-grade specification for the third product line. The
> preventative complement to the demurrage recovery product: watch active
> voyages while they are in flight and tell the customer when the calendar
> is about to cost them money.
>
> Pitch in [product_roadmap.md §4.2](product_roadmap.md). This document is
> the build spec.

---

## 0. The one-paragraph version

Today our pipeline runs after a voyage has finished, when the laytime is
already blown and the question is "how much can we recover." Claims Radar
runs while the voyage is in flight, every fifteen minutes: it ingests AIS
position, port-authority berth status, weather at the discharge port, and
any operator email forwarded through §2.3, and answers two questions:

1. "How much laytime allowance is left, given what has actually happened
   so far?"
2. "Given the projected next few hours, when does this voyage tip from
   compliant to on demurrage, and how much does each hour cost?"

The output reuses the existing `FlaggedEvent` shape with a
`predicted: bool = True` marker, so the case-detail surface renders future
events the same way it already renders past ones.

---

## 1. Goals + non-goals

### Goals (v0.1 → v1.0)

- A workspace dashboard `/monitor` listing every active voyage with its
  current exposure colour (Green / Amber / Red) and projected EUR loss.
- A per-voyage `/monitor/<voyage_id>` timeline showing the AIS position,
  port queue position, weather predictions, and the predicted-event list.
- Alerts via email (and optional SMS on Enterprise) when a configurable
  threshold is crossed.
- The same auditable Strong / Arguable / Weak framing the analyst uses for
  finished claims (§1.5 sub-scores), so the predicted event reads in the
  same vocabulary as the post-hoc one.

### Non-goals

- We do **not** route the vessel. Route optimisation is saturated and out
  of our edge (see product_roadmap.md §4.3).
- We do **not** sell AIS access. The customer uses our integration to read
  positions for *their* vessels; we do not resell the feed.
- No master / crew chat. The operator is the user; the master is not.
- No predictive ETA model better than the AIS provider's. We trust Spire's
  ETA and reason about what it implies for laytime.

---

## 2. Data sources

Each source has a settings flag (`monitor_<source>_live`) so a fresh
environment runs offline against committed fixtures. Production flips the
flags one at a time.

### 2.1 AIS — Spire (primary)

- Endpoint: `https://api.spire.com/v2/vessel-pulses` (their own product
  name varies by package; the keep-alive REST endpoint that returns the
  most recent position by IMO is what we wire).
- Auth: bearer token in env (`SPIRE_API_TOKEN`).
- Cost: tier-dependent, plan around €0.50 per vessel-day at our scale.
- Rate limit: 5 req/sec sustained; the egress adapter (§1.6 `outbound.py`)
  is reused unchanged.
- Cache: 60 seconds on the position endpoint; AIS does not update faster
  than that in their feed.
- Fall-back: MarineTraffic API for cheaper coverage when Spire is
  unavailable for a vessel; not implemented in v0.1.

What we use: position (lat, lon, course, speed, heading), time, ETA at
next port, voyage destination.

### 2.2 Weather — Open-Meteo (free)

- Endpoint: `https://api.open-meteo.com/v1/forecast`.
- Auth: none.
- Rate limit: 600 req/minute (well above our needs).
- Cache: 60 minutes per port; weather forecasts do not change usefully
  faster.

What we use: precipitation (mm/hr) and wind (m/s) forecasts for the next
24 hours at the discharge port. Used to predict weather stoppages that
would qualify under the CP's weather exception clause (we know the
threshold from the CP extraction).

### 2.3 Port-authority berth feeds (port-specific)

A small adapter per port. v0.1 covers the four busiest:

- **Rotterdam:** Port of Rotterdam Authority — Portbase has a paid API
  with berth availability and vessel queue position. Phase 2.
- **Singapore:** MPA digitalPORT (free).
- **Antwerp:** APICS (subscription).
- **Hamburg:** HVCC Hafenverkehrszentrale (free, scraping required).

Each adapter implements:

```python
class PortFeed(Protocol):
    async def berth_status(self, imo: str) -> Optional[BerthStatus]: ...
    async def queue_position(self, imo: str, port: str) -> Optional[int]: ...
```

`BerthStatus` is `{state: "anchored" | "shifting" | "berthed", since:
datetime}`. Routes that have no implementation fall back to "unknown,"
which is rendered as a grey chip on the UI.

### 2.4 Email-in (§2.3)

Operator forwards from the port agent, the broker, the master himself.
Already wired. The monitor agent reads recent emails for the voyage and
extracts free-text events (e.g. "expecting all-fast at 0400 LT") that
plug into the timeline.

---

## 3. The data model

Three new feature-local Pydantic modules; no change to frozen `schemas.py`.

### 3.1 New tables

```
voyage_monitoring (
    voyage_id PK FK,
    enabled BOOLEAN DEFAULT TRUE,
    enrolled_at TIMESTAMP,
    last_run_at TIMESTAMP NULLABLE,
    next_due_at TIMESTAMP,
    exposure_eur FLOAT DEFAULT 0,
    exposure_state VARCHAR DEFAULT 'green',  -- green | amber | red | done
    last_ais_position JSONB,
    cached_weather JSONB,
    cached_berth_status JSONB
)

voyage_monitor_events (
    id PK,
    voyage_id FK,
    seq INTEGER,
    kind VARCHAR,            -- closed Literal below
    predicted BOOLEAN,
    confidence VARCHAR,      -- Strong | Arguable | Weak
    at TIMESTAMP,
    payload JSONB,
    cited_authorities JSONB
)

monitor_alert_rules (
    id PK,
    workspace_id FK,
    rule_kind VARCHAR,       -- closed Literal: eur_loss | hours_idle |
                             -- weather_exception | berth_queue
    threshold_value FLOAT,
    channels VARCHAR,        -- comma-separated: email | sms | webhook
    recipients VARCHAR,      -- comma-separated email addresses
)

monitor_alert_deliveries (
    id PK,
    rule_id FK,
    voyage_id FK,
    delivered_at TIMESTAMP,
    channel VARCHAR,
    payload JSONB
)
```

### 3.2 The monitor event vocabulary (closed)

```python
MonitorEventKind = Literal[
    "ais_position",            # position update
    "berth_change",            # arrived/anchored/shifted/berthed
    "weather_prediction",      # forecast crosses a CP threshold
    "weather_now",             # current weather exceeds the threshold
    "port_queue_change",       # queue position moved
    "email_received",          # operator forwarded a relevant email
    "laytime_threshold",       # vessel is now on demurrage (predicted/actual)
    "off_hire_risk",           # cumulative idle time exceeds CP allowance
    "alert_fired",             # one of our rules triggered an alert delivery
]
```

### 3.3 The predicted flagged event

```python
class PredictedFlaggedEvent(FlaggedEvent):
    """Extends the analyst's FlaggedEvent with a marker that this row is a
    projection, not a fact. The frozen FlaggedEvent stays a base; we
    subclass locally so the surface treats predicted and actual rows the
    same way."""

    predicted: bool = True
    predicted_at: datetime
    horizon_minutes: int       # how far ahead this prediction looks
    cited_authorities: list[CitedAuthority]
```

The `cited_authorities` field hangs off every prediction the same way it
hangs off post-hoc dispute analysis. Same legal subsystem (§1.6), same
verification gate, same citation token format.

---

## 4. The pipeline

```
[ cron tick: every 15 min, per active voyage ]
                │
                ▼
   Fan-out async tasks (asyncio.gather):
   - ais.get_position(imo)
   - weather.forecast(discharge_port)
   - port_feed.berth_status(imo, discharge_port)
   - inbox.recent_events(voyage_id, since=last_run_at)
                │
                ▼
        Agent M1: MonitorAgent (Sonnet 4.6, tool-using)
        Inputs: voyage state + 4 above + factor tables
        Tools:
          - search_case_corpus / lookup_imo_convention (§1.6, reused)
          - voyage_clock(at=now)              [computes hours used so far]
          - weather_exception_threshold(cp)   [reads from extraction]
        Output (structured):
          - ExposureSummary: state + exposure_eur + reasoning
          - list[PredictedFlaggedEvent]: 0..N rows
                │
                ▼
   compute_exposure_eur()  (Python, deterministic)
   exposure_eur = max(0, predicted_demurrage - allowance_remaining)
   exposure_eur is recomputed even if the model proposed a number;
   the model never owns money (matches the demurrage rule).
                │
                ▼
   persist: voyage_monitoring updates, monitor_events appended
                │
                ▼
   evaluate_alert_rules()  (Python)
   For each MonitorAlertRule in the workspace whose threshold is crossed
   AND has not been delivered for this voyage today, enqueue an alert.
                │
                ▼
   deliver_alerts()  (SES from §1.3 + optional SMS)
```

### 4.1 Agent M1 — MonitorAgent

System prompt highlights:

- "You are reading the live state of one voyage. The vessel is at <pos>;
  the discharge port is <P> at distance <D> NM; the CP weather clause
  threshold is <T> mm/hr; the operator forwarded <K> emails since you
  last looked."
- "Output 0..N predicted events. Each event is one of the closed kinds.
  Every event whose proposition is a legal one (e.g. 'the weather
  exception will apply') MUST carry a `cited_authority` whose
  `verified_via_tool=True`."
- "Money is never your output. The route layer recomputes
  `exposure_eur` from your prediction list."

The tool-use loop reuses the §1.6 verification gate verbatim. The agent
typically runs in under five seconds; cost-per-tick is ~€0.001 on Sonnet
4.6 with prompt caching on the cross-cutting prefix.

### 4.2 The cron

v0.1: APScheduler in-process, one job per 15 minutes per active voyage.
Stored in a tiny SQL table so a restart picks up where it left off.

v0.2: move to AWS EventBridge + a dedicated Lambda when we have more than
~500 active voyages (APScheduler in-process scales fine to that point).

### 4.3 Exposure colour + EUR

```python
def compute_exposure_eur(voyage, predictions) -> tuple[ExposureState, float]:
    laytime_remaining_h = voyage.laytime.laytime_allowed_hours - hours_used_so_far(voyage)
    predicted_demurrage_h = sum(
        p.duration_h for p in predictions if p.kind == "laytime_threshold"
    )
    if predicted_demurrage_h <= 0:
        return "green", 0.0
    rate = voyage.laytime.demurrage_rate_per_hour_eur
    exposure = max(0.0, predicted_demurrage_h * rate)
    if exposure < 5000:
        return "amber", exposure
    return "red", exposure
```

Thresholds (5000 EUR amber / red split) are configurable per workspace
once the settings UI lands.

### 4.4 Alert delivery

Reuses the §1.3 SES send adapter. Subject line carries the vessel name +
EUR figure; body is a short Markdown summary; the case-detail URL is
included so the recipient lands one click away. Deduplication: an alert
for the same rule + voyage fires at most once per 6 hours unless the
exposure_eur increases by more than the threshold step.

---

## 5. Wire models (feature-local)

```python
class AisPosition(BaseModel):
    imo: str
    lat: float
    lon: float
    course_deg: float
    speed_knots: float
    heading_deg: Optional[float]
    eta_at_discharge: Optional[datetime]
    fetched_at: datetime


class WeatherForecast(BaseModel):
    port: str
    fetched_at: datetime
    hourly: list[WeatherHour]


class WeatherHour(BaseModel):
    at: datetime
    precipitation_mm_per_hr: float
    wind_m_per_s: float


class BerthStatus(BaseModel):
    state: Literal["anchored", "shifting", "berthed", "underway", "unknown"]
    since: Optional[datetime]
    queue_position: Optional[int]


class ExposureSummary(BaseModel):
    voyage_id: str
    state: Literal["green", "amber", "red", "done"]
    exposure_eur: float
    headline: str         # one-line: "On demurrage in 4h13m at current discharge rate"
    drivers: list[str]    # short bulleted explanations
    cited_authorities: list[CitedAuthority]


class MonitorAlertRule(BaseModel):
    id: int
    workspace_id: str
    rule_kind: Literal["eur_loss", "hours_idle", "weather_exception", "berth_queue"]
    threshold_value: float
    channels: list[Literal["email", "sms", "webhook"]]
    recipients: list[str]
```

---

## 6. Routes

```
POST   /voyages/{voyage_id}/monitor/enable          - enrol voyage in radar
POST   /voyages/{voyage_id}/monitor/disable         - drop from cron
GET    /monitor                                     - workspace dashboard
GET    /monitor/{voyage_id}                         - per-voyage timeline
GET    /monitor/{voyage_id}/events                  - paginated event log

GET    /monitor/alerts                              - list rules
POST   /monitor/alerts                              - create a rule
DELETE /monitor/alerts/{rule_id}                    - remove a rule
GET    /monitor/alerts/deliveries                   - last 100 deliveries

POST   /internal/monitor/tick                       - cron entrypoint
                                                       (HMAC-signed like §2.3)
```

Auth: every read route `require_workspace_role("member")`; rule mutation
`require_workspace_role("admin")`; the cron entrypoint is HMAC-signed
with `MONITOR_CRON_SHARED_SECRET`, identical pattern to the inbound mail
route.

Audit: each enable/disable + rule create/delete writes a row; alert
deliveries also write a row so the customer can see who got notified for
what and when.

---

## 7. Frontend

New route group `/monitor`. Components under `apps/web/components/monitor/`:

- `RadarDashboard.tsx` — table of active voyages with a coloured chip
  (Green / Amber / Red), exposure EUR figure, vessel + port + ETA, and a
  one-line headline from `ExposureSummary.headline`.
- `VoyageRadarTimeline.tsx` — vertical timeline of `monitor_events` rows,
  with a small map showing the AIS position and a 24-hour weather strip
  under the discharge port name.
- `ExposureCard.tsx` — the headline + drivers panel.
- `AlertsSettings.tsx` — create/list rules; recipient pickers; thresholds.
- `EnableMonitorButton.tsx` — on the case detail surface, a one-click
  enrol that flips the voyage into the cron.

The page reuses the existing skeleton + Reveal pattern; no new design
primitives.

---

## 8. Tests

### Synthetic active voyage

Committed fixture: a voyage extracted from the Rotterdam scenario but
with the SoF truncated to half-finished. AIS + weather + berth mocks
committed under `apps/api/tests/data/monitor/`. Lock:

- `compute_exposure_eur` returns ("amber", < 5000) at horizon T=0.
- After 4 hours of stayed weather, the predicted event list adds a
  `laytime_threshold` row and the exposure moves to "red".

### Alert dedup

Two ticks within 6 hours of each other against the same crossed
threshold produce exactly one alert delivery row.

### Citations gate

Predictions that cite a non-existent case are dropped by the §1.6
verifier. Locked with a fixture transcript.

### Cron interruption recovery

Simulate the process dying mid-tick. After restart, the cron picks up the
voyage on its next scheduled `next_due_at` rather than re-running every
voyage. `voyage_monitoring.last_run_at` is the source of truth.

---

## 9. Operational concerns

- **AIS cost guardrails.** A per-workspace cap on active monitored
  voyages keyed by pricing tier. The radar dashboard surfaces the cap so
  the customer knows when they need to upgrade.
- **Alert fatigue.** 6-hour dedup window, EUR-step rule (don't re-alert
  unless exposure grew by N EUR). Customer can tune both.
- **PII.** AIS position data is not PII; berth status is operational.
  Email-in content is captured in audit-class redacted form (sender
  domain, attachment count, no body).
- **Cron correctness under deploy.** The scheduler writes `next_due_at`
  to the DB; a restart resumes correctly. Lambda + EventBridge follow-up
  removes the in-process scheduler entirely.
- **Network outage on Spire.** Position cache TTL extends to 6 hours
  during a Spire outage so the dashboard does not flap; outage banner
  surfaces on the UI when the cache age > 30 minutes.
- **Customer disables monitoring mid-voyage.** Disable is soft: the
  voyage_monitoring row stays with `enabled=False` so re-enable picks
  the history back up; no rerun of past ticks.

---

## 10. Phasing

| Phase | Scope | Outcome |
| --- | --- | --- |
| **A (3-4 weeks)** | Cron + MonitorAgent + AIS via Spire (Open-Meteo weather free). Dashboard + per-voyage timeline. One workspace alert rule kind: `eur_loss`. | One paying design partner runs the radar on three vessels. |
| **B (+1 week)** | Port-feed adapter for Rotterdam (Portbase). | Berth-queue rule kind; queue-change events on the timeline. |
| **C (+2 weeks)** | Three more port adapters (Singapore, Antwerp, Hamburg). | Most major EU/Med ports covered. |
| **D (+1 week)** | SMS via SNS, webhook channel, more alert rule kinds. | Enterprise tier. |
| **E (later)** | EventBridge + dedicated Lambda for the cron; multi-workspace scale. | Removes APScheduler. |

End to end: ~5-7 weeks to first paying partner per the roadmap.

---

## 11. Owners

- Backend (sections 3-6, 8, 9): dkall.
- Frontend (section 7): Roman.
- Infra (Spire account, port-feed subscriptions where needed, the cron
  scheduler decision and budget): Panos.

---

## 12. Risk register

| Risk | Mitigation |
| --- | --- |
| Spire API cost spike | Cap voyages per tier; long-cache AIS positions; per-vessel rate-limit at the egress adapter. |
| Port-feed scraping breaks on layout change | Per-feed integration tests against a small recorded fixture; one feed broken does not break the rest. |
| Alert spam ruins the customer experience | Dedup window + EUR-step rule + per-rule pause toggle in the settings UI. |
| Wrong predictions in the timeline reduce trust | Every prediction carries a `confidence` word + a `cited_authority`; the UI labels predictions as such and the dashboard's exposure_eur is recomputed in Python. |
| Cron drift under load | `next_due_at` in the DB, idempotent ticks, soft fail with logged backlog. |
| Customer perceives privacy concern over the AIS feed | The data is public via T-AIS; we never store more than position + ETA, and we audit-log every fetch. |
| The product cannibalises the demurrage product's recovery fees | Pricing model deliberately splits: monitoring is recurring (per-vessel/month) on top of the per-claim fees. Both lines coexist. |

---

## 13. What is deliberately not in this plan

- Off-hire monitoring under time charters (NYPE 93). Different doc shape;
  revisit after the voyage-charter version is stable.
- Bunker telemetry. Year-2 sub-product.
- A native mobile app for masters/operators. Year-2 follow-up.
- A predictive AIS ETA better than Spire's. Out of our edge.
- Voluntary cargo-damage detection (vibration/temperature sensors). Out
  of scope.
