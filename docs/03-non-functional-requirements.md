# Copy-Item Flow — Non-Functional Requirements (MVP)

## 3.1 Performance
**Goal:** Fast enough for day-to-day use; predictable under load.

- **NFR-P1 (Single item latency)**  
  *Rationale:* Operators shouldn’t wait.  
  **AC:** For lists ≤5,000 items, a non-bulk upsert/update/create with ≤10 mapped fields and no attachments completes in ≤5 s (p50) and ≤10 s (p95).

- **NFR-P2 (Attachments)**  
  **AC:** Copying ≤10 attachments totaling ≤25 MB adds ≤20 s (p95). Failures on individual files do not fail the run; they’re logged as warnings.

- **NFR-P3 (Bulk updates)**  
  **AC:** With `bulk=true`, end-to-end runtime scales roughly linearly: ≤0.8 s per item (p50), ≤1.5 s per item (p95) for 100 matched items, excluding attachment work.

- **NFR-P4 (Transforms overhead)**  
  **AC:** Applying up to 3 transforms per field (`ensureUser`, `toUTC`, `lookupByText`) increases per-item time by ≤30% (p95).

---

## 3.2 Reliability & Resilience
**Goal:** Complete the job or fail fast; tolerate transient SPO hiccups.

- **NFR-R1 (Retry policy)**  
  **AC:** All HTTP calls use retry on 429/5xx with exponential backoff (min 1 s, max 30 s, 3 attempts). Final failure is recorded with endpoint and status.

- **NFR-R2 (Idempotent update)**  
  **AC:** Update paths are idempotent at the item level: re-running with the same inputs does not duplicate items; only mapped fields change.

- **NFR-R3 (Partial tolerance)**  
  **AC:** Field-level errors (type mismatch, missing dest field, transform error) skip that field and continue; run finishes with a non-fatal warning.

- **NFR-R4 (Fail-fast guards)**  
  **AC:** Invalid JSON, unreachable site, or missing list causes termination before any write.

---

## 3.3 Availability & Operability
**Goal:** Routine use during business hours without babysitting.

- **NFR-A1 (Operational hours)**  
  **AC:** Flow is callable 24×7; no time-of-day assumptions. (SPO throttling may slow; not break.)

- **NFR-A2 (Connection references)**  
  **AC:** Uses managed connection references only; rotating the reference requires no flow edits.

---

## 3.4 Security & Privacy
**Goal:** Least privilege; no sensitive leakage.

- **NFR-S1 (Least privilege)**  
  **AC:** The SharePoint connection has read on source and contribute on destination—no site collection admin rights.

- **NFR-S2 (No secrets in logs)**  
  **AC:** Output/log never includes bearer tokens or raw cookies; emails appear only when necessary for `ensureUser`, and not persisted beyond run artifacts.

- **NFR-S3 (PII handling)**  
  **AC:** Person fields are processed transiently; logs redact to user principal name or a one-way hash if configured (optional switch, default off for MVP).

- **NFR-S4 (Tenant boundary)**  
  **AC:** Same-tenant only; any cross-tenant target is rejected with clear error.

---

## 3.5 Observability (No “loglevel” input)
**Goal:** Always enough breadcrumbs to debug, without noisy knobs.

- **NFR-O1 (Standard output shape)**  
  **AC:** Each run returns JSON with: `operation`, `bulk`, `quickMatch`, `destMatch`, `matchedCount`, `createdIds[]`, `updatedIds[]`, `warnings[]`, `errors[]`.

- **NFR-O2 (Key breadcrumbs)**  
  **AC:** Output includes a compact decision trail: matching mode and criteria summary (redacted), transforms applied per field (names only), attachment summary (added/overwritten/skipped counts).

- **NFR-O3 (Optional run log sink)**  
  **AC:** If an environment variable `COPYITEM_RUNLOG_LIST` is present, the flow appends a run summary row; otherwise, it skips without error.

---

## 3.6 Compatibility & Constraints
**Goal:** Work on common SPO list shapes without magic.

- **NFR-C1 (Supported types)**  
  **AC:** Text, Note, Number, Currency, Boolean, DateTime, URL, Choice/ChoiceMulti, Lookup/LookupMulti, Person/PersonMulti are supported per FR-9.

- **NFR-C2 (Unsupported types in MVP)**  
  **AC:** Taxonomy columns and Document Sets are detected and skipped with clear warnings (documented).

- **NFR-C3 (Large lists)**  
  **AC:** Matching supports paging; CAML and OData paths handle lists >5k items via server-side filtering.

---

## 3.7 Maintainability & Extensibility
**Goal:** Extend features without breaking the contract.

- **NFR-M1 (Stable input contract)**  
  **AC:** Trigger inputs remain unchanged; all future features fit inside `settings` or are read from environment variables.

- **NFR-M2 (Transform registry)**  
  **AC:** Transforms implemented via a single switch/dispatcher so adding a new transform doesn’t touch mapping logic.

- **NFR-M3 (Schema versioning)**  
  **AC:** `settings.version` is checked; backward-compatible changes are allowed; breaking changes are rejected with a descriptive message.

---

## 3.8 Usability
**Goal:** Non-technical users succeed without reading a book.

- **NFR-U1 (Defaults)**  
  **AC:** Trigger defaults produce a safe no-op match (e.g., `ID eq -1` in settings) and `attachmentMode=none`.

- **NFR-U2 (Quick match coverage)**  
  **AC:** `destMatchColumn` + `destMatchValue` handles at least 80% of simple upserts; the UI labels explain it in ≤1 line each.

- **NFR-U3 (Helpful failures)**  
  **AC:** Error messages name the field/list/site in question and the exact cause (e.g., “Destination field ‘Owner’ not found”).

---

## 3.9 Internationalization & Time Zones
**Goal:** Date/time correctness across locales.

- **NFR-I1 (UTC normalization)**  
  **AC:** All outbound DateTime values are ISO-8601 UTC. If no `toUTC` transform is provided, the flow does not guess time zones; it logs a warning when writing local-looking timestamps.

- **NFR-I2 (Culture-safe parsing)**  
  **AC:** Numeric and date parsing is culture-invariant; commas/periods in numbers are normalized where possible or rejected with a clear warning.

---

## 3.10 Limits & Safeguards
**Goal:** Prevent accidental blast radius.

- **NFR-L1 (Bulk safety)**  
  **AC:** If `bulk=true` and `matchedCount` > 1000, the flow aborts with a protective error unless an environment variable `COPYITEM_ALLOW_LARGE_BULK=true` is set.

- **NFR-L2 (Attachment cap)**  
  **AC:** Per item, process a maximum of 50 attachments or 100 MB total; excess are skipped with warnings.

- **NFR-L3 (Map size cap)**  
  **AC:** Reject map arrays with >200 entries to avoid runaway payloads.


### Update: Added reliability expectations (retries, warnings, attachment cap handling).
