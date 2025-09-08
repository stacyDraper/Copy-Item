# Copy-Item Flow — One-Page Design Brief (Expanded MVP)

## Problem
Teams need a reusable, predictable way to copy SharePoint list items — including complex field types and attachments — across sites/lists in the same tenant. Current ad‑hoc approaches are inconsistent, fragile with People/Lookup fields, and unclear about create vs. update behavior.

---

## Goals
- One standardized flow usable across lists/sites in the tenant.
- Simple for casual users; powerful for advanced cases via **settings** JSON.
- Reliable handling for single & multi: **People, Lookup, Choice**; plus **DateTime, URL, text/number**.
- Clear, safe semantics for **create / update / upsert**, including **bulk updates**.
- Stable input contract that remains forward‑compatible.

---

## In Scope (MVP)
- Manual trigger (and “For a selected item/document” context).
- **Operations:** `create`, `update` (update-only; error if no match), `upsert`.
- **Matching:**
  - Quick match via trigger fields **`destMatchColumn` + `destMatchValue`**.
  - Advanced match via **`settings.match`** (`simple` / `odata` / `caml`).
  - **Bulk updates:** `bulk=true` updates all matches (for update/upsert).
- **Mapping engine** with `source` / `dest` / `default` / `when` / `transform` / `typeHint`.
- **Transforms (MVP set):** `ensureUser`, `toUTC`, `stripHTML`, `lookupByText`.
- **Field support:**
  - **People:** single & multi (resolve via `ensureUser`).
  - **Lookup:** single & multi (IDs or `lookupByText` on display).
  - **Choice:** single & multi.
  - **DateTime** (ISO‑8601 UTC), **URL**, **text/number**.
- **Attachments:** `none`, `append`, `overwrite`, `replace`.
- **Outputs:** structured log + arrays of `createdIds` / `updatedIds`, `matchedCount`, `warnings` / `errors`.

---

## Out of Scope (for now)
- Profile‑based connections / centralized **Jobs** list.
- Cross‑list‑type copies (e.g., doc library ↔ list, calendar, pages).
- Very complex multi‑condition match builders in the UI (supported via **settings JSON** only).
- Rich exportable reports.

---

## Users & Usage Modes
- **Operators:** fill basic fields (`map`, quick match) and run; often from a selected item.
- **Power Users:** paste **settings JSON** for OData/CAML filters or advanced behavior.
- **Developers/Admins:** maintain/extend transforms; manage deployment and guardrails.

---

## Success Criteria
- Majority of real workloads run using only trigger inputs (`map` + quick match) without editing JSON.
- Correct, consistent writes for **People/Lookup/Choice** (single & multi) across typical lists.
- **Upsert** and **update‑only** semantics behave exactly as documented; **bulk updates** touch all matches.
- Flow returns IDs and a useful log on every run.
- Contract remains stable as features evolve.

---

## Risks & Assumptions
- **Risk:** Large lists, heavy bulk, or big attachments may trigger throttling — handled via retries/backoff.
- **Risk:** `lookupByText` depends on unique or well‑scoped display values — collisions are warned.
- **Assumption:** Same‑tenant access with appropriate permissions via connection reference.
- **Assumption:** Destination schema known/compatible; unmapped or missing fields are skipped with warnings.
