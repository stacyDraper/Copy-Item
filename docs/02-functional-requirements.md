# Copy-Item Flow — Functional Requirements (Updated MVP)

## FR-1 Trigger & Inputs
**Description:** Manual trigger with optional context from “For a selected item/document.”

**Acceptance Criteria (AC):**
- **AC-1.1: Inputs:**
  - `sourceSiteUrl`, `sourceListName`, `destSiteUrl`, `destListName` — Required. Full URLs for source and destination sites, plus list names.
  - `sourceItemId` — Optional. Numeric ID of the source item.
  - `map` — JSON array defining how fields in the source map to fields in the destination.
  - `operation` — One of: `create` | `update` | `upsert`.
  - `destMatchColumn`, `destMatchValue` — Optional quick match parameters.
  - `attachmentMode` — One of: `none` | `append` | `overwrite` | `replace`.
  - `mapOnly` — Yes/No. If `Yes`, only mapped fields are copied.
  - `settings` — Optional JSON for advanced matching and options.
- **AC-1.2:** If triggered via “For a selected item/document,” `sourceItemId` is auto-populated from context.
- **AC-1.3:** If required fields are missing, flow fails immediately with the missing field name in the error.

---

## FR-2 Input Validation
**Description:** Ensure all trigger and settings inputs are valid before proceeding.

**AC:**
- Validate that all required text fields are non-empty and well-formed.
- Verify `sourceSiteUrl` and `destSiteUrl` are valid URLs.
- Check that `sourceListName` and `destListName` exist in the specified sites.
- Parse and validate JSON inputs (`map`, `settings`) to ensure correct syntax and required keys.
- Confirm that `operation`, `attachmentMode`, and `mapOnly` values are valid choices.

---

## FR-3 Operation Modes
**Description:** Flow can create, update-only, or upsert destination items.

**AC:**
- **AC-3.1:** `create` → Always creates a new item in the destination.
- **AC-3.2:** `update` → Match is required; if no match, fail with “No match found.”
- **AC-3.3:** `upsert` → Match; if found, update; if not found, create new.
- **AC-3.4:** Works with both quick match and advanced match modes.

---

## FR-4 Mapping Engine
**Description:** Build the update payload dynamically based on the provided `map`.

**AC:**
- Each `map` entry defines:
  - `source` — Internal name of the source field.
  - `dest` — Internal name of the destination field.
  - Optional: `default`, `when`, `transform`, `typeHint`.
- Skip mapping if destination field does not exist or is not editable.
- Preserve unmapped fields in the destination.

---

## FR-5 Transforms (Expanded)
**Description:** Transform support for all MVP field types.

**AC:**
- **AC-5.1:** `ensureUser` works with single and multi-Person fields.
- **AC-5.2:** `toUTC` converts date/time fields (single and multi) to ISO-8601 UTC format.
- **AC-5.3:** `stripHTML` removes HTML tags from text and choice fields.
- **AC-5.4:** `lookupByText` resolves lookup values by display text if ID is not provided.
- **AC-5.5:** Multiple transforms can be applied in sequence; failures generate warnings but do not stop the run.

---

## FR-6 Quick Match (Trigger Fields)
**Description:** Auto-build match criteria when both quick match parameters are provided.

**AC:**
- If `destMatchColumn` and `destMatchValue` are both set, the flow builds an internal `settings.match` object automatically.
- Matching uses equality on the specified column/value.

---

## FR-7 Advanced Match (`settings.match`)
**Description:** Supports complex matching via settings JSON.

**AC:**
- Accepts `simple` (JSON key/value), `odata` (OData filter string), or `caml` (CAML XML string) formats.
- Allows `bulk=true` to update all matching items.
- Validates filter syntax before executing.

---

## FR-8 Attachments
**Description:** Copy attachments from source to destination based on mode.

**AC:**
- `none` — Do not copy attachments.
- `append` — Copy attachments from source only if not present in destination.
- `overwrite` — Replace attachments in destination with same name from source.
- `replace` — Remove all attachments in destination, then copy all from source.

---

## FR-9 Special Field Types (Expanded MVP)
**Description:** Full support for single & multi-value People, Lookup, and Choice fields.

**AC:**
- **AC-9.1:** Person (single) — Resolve via `ensureUser`.
- **AC-9.2:** Person (multi) — Accepts array of emails/logins or resolves via `ensureUser` in batch.
- **AC-9.3:** Lookup (single) — Supports ID or display text via `lookupByText`.
- **AC-9.4:** Lookup (multi) — Accepts array of IDs or display texts; resolves all before writing.
- **AC-9.5:** Choice (single) — Writes valid choice value directly.
- **AC-9.6:** Choice (multi) — Accepts array of valid values; writes in SharePoint multi-choice format.
- **AC-9.7:** DateTime — Writes ISO-8601 UTC.
- **AC-9.8:** URL — Writes `{Url, Description}` or plain URL string.

---

## FR-10 Write Operation (Bulk Included)
**Description:** Safe write for single and multiple matches.

**AC:**
- **AC-10.1:** `bulk=false` → Update first match only.
- **AC-10.2:** `bulk=true` → Update all matches; if no matches and operation is `upsert`, create new.
- **AC-10.3:** All updates use `ValidateUpdateListItem` or PATCH to preserve unmapped fields.

---

## FR-11 Output Contract
**Description:** Structured output for each run.

**AC:**
- `createdIds` — Array of created item IDs.
- `updatedIds` — Array of updated item IDs.
- `matchedCount` — Number of matched destination items.
- Includes attachment summary, warnings, and errors.

---

## FR-12 Logging
**Description:** Maintain a clear log for each run.

**AC:**
- Log includes all actions taken, skipped fields, and transform warnings.
- Bulk operations include a `bulk=true` flag in the summary.

---

## FR-13 Error Handling & Resilience
**Description:** Flow must fail fast on invalid inputs, but recover from transient errors.

**AC:**
- Immediate failure on invalid site/list/field names.
- Skip and warn for missing fields, transform errors, or ambiguous lookups.
- Retry on 429/5xx errors with exponential backoff.

---

## FR-14 Performance Targets
**Description:** Flow should complete in a reasonable time frame.

**AC:**
- Bulk update performance is measured as total elapsed time / items updated.
- Avoids unnecessary API calls by skipping unmapped fields and unchanged values.

---

## FR-15 Security & Permissions
**Description:** Ensure the flow respects SharePoint permissions.

**AC:**
- Connection account must have read access to source and write access to destination.
- No elevation of privileges within the flow.

---

## Deferred List (Shortened)
- Profile-based connections.
- Jobs list.
- Cross-list type copies.
- Complex multi-condition match rules.
- Rich reporting/export to file.


### Update: Stage 5 now includes retry + warning logic, Stage 6 enforces attachment caps, Stage 7 exposes outputs.
