# Copy-Item Flow — Test Plan (MVP)

## 6.1 Scope & Traceability
- **Covers**: FR-1…FR-15 and NFRs in #3.
- **Out of scope (now)**: Profiles/Jobs list, cross-list-type copies, rich reporting.
- **Traceability key**: Each test case lists the FR/NFR it verifies.

---

## 6.2 Environments & Data
- **Env**: SPO test tenant with your representative lists from #4 (Tasks, Projects, Inventory + Departments, Vendors).
- **Connection**: Service account with Read (source) + Contribute (dest).
- **Data reset**: Before each suite, reset lists to the baseline seed (keep a small “golden backup” list or CSV to repopulate).

---

## 6.3 Smoke Suite (run first on every build)

| ID     | Name             | Inputs (summary)                                         | Expected                                      | Verifies                  |
|--------|------------------|----------------------------------------------------------|-----------------------------------------------|---------------------------|
| SMK-01 | Create basic     | operation=create, map Title→Title, no attachments        | 1 item created, createdIds[0] present         | FR-1, FR-3.1, FR-10.3, FR-11 |
| SMK-02 | Upsert quick match | operation=upsert, destMatchColumn=Title, destMatchValue=Task-001 | 1 item updated, matchedCount=1, updatedIds[0] | FR-6, FR-3.3, FR-11 |
| SMK-03 | Attach append    | attachmentMode=append, source has 2 files                | 2 attachments added, no errors                | FR-8.2 |
| SMK-04 | Person ensureUser | Map AssignedToEmail→Owner, transform ensureUser          | Owner set to correct user                     | FR-5.1, FR-9.1 |
| SMK-05 | Multi-choice write | Map Tags[]→Tags (multi)                                 | Values written; verify UI                     | FR-9.6 |

---

## 6.4 Functional Matrix

### A) Operations & Matching

| ID    | Case                     | Inputs (key params)                                     | Expected Result                             | Verifies             |
|-------|--------------------------|----------------------------------------------------------|----------------------------------------------|----------------------|
| OP-01 | Create always             | operation=create, minimal map                           | New item; matchedCount=0; createdIds[0]      | FR-3.1               |
| OP-02 | Update-only: single match | operation=update, quick match Title=Task-002            | Updates existing; updatedIds[0]; no creates  | FR-3.2, FR-6         |
| OP-03 | Update-only: no match     | operation=update, quick match to a nonexistent value    | Fail with “No match found”; no writes        | FR-3.2               |
| OP-04 | Upsert: no match          | operation=upsert, quick match to nonexistent            | Creates new item; createdIds[0]              | FR-3.3               |
| OP-05 | Upsert: multiple matches  | operation=upsert, quick match “Status=Active” (2 items) | Updates first; matchedCount=2; warning       | FR-6.3, FR-7.5, FR-11 |

### B) Advanced Matching (`settings.match`)

| ID    | Case                       | Inputs                                                        | Expected                        | Verifies         |
|-------|----------------------------|---------------------------------------------------------------|-----------------------------------|------------------|
| AM-01 | settings.simple (equality) | settings.match={mode:"simple",criteria:{Title:"Task-003"}}    | Updates matching item             | FR-7.1           |
| AM-02 | settings.simple (range)    | Modified >= date                                              | Updates first; logs criteria      | FR-7.1, NFR-O2   |
| AM-03 | settings.odata              | $filter=Status eq 'Active' and Category eq 'Hardware'        | Updates first match               | FR-7.2           |
| AM-04 | settings.caml               | `<View><Query>…</Query></View>`                              | Updates first match               | FR-7.3           |
| AM-05 | Precedence over quick match | Provide quick match + settings.match                         | settings wins                     | FR-6.2           |

### C) Bulk Updates

| ID    | Case                   | Inputs                                                     | Expected                           | Verifies  |
|-------|------------------------|------------------------------------------------------------|-------------------------------------|-----------|
| BK-01 | Bulk simple            | operation=update, settings.match.bulk=true, 3 matches     | All 3 updated; updatedIds.length=3  | FR-10.2   |
| BK-02 | Bulk upsert none found | operation=upsert, bulk=true, no matches                    | Creates 1 new; createdIds.length=1  | FR-10.2   |
| BK-03 | Bulk safety cap        | Match >1000 (seed mock)                                    | Run aborts unless override enabled  | NFR-L1    |

### D) Attachments

| ID    | Case               | Inputs                                       | Expected                       | Verifies  |
|-------|--------------------|----------------------------------------------|---------------------------------|-----------|
| AT-01 | none               | attachmentMode=none                          | No attachment calls             | FR-8.1    |
| AT-02 | append new         | Source has A,B; dest none                     | A,B added                       | FR-8.2    |
| AT-03 | append skip dupes  | Source A,B; dest A                            | B added; warning for A           | FR-8.2    |
| AT-04 | overwrite          | Source A; dest A                              | Dest A replaced                  | FR-8.3    |
| AT-05 | replace            | Source A,B; dest X,Y                          | X,Y removed; A,B added           | FR-8.4    |
| AT-06 | large file warn    | One file >25MB                                | Warn or slow add; run continues  | NFR-P2    |

### E) Mapping: Defaults, When, MapOnly

| ID    | Case             | Inputs                                  | Expected           | Verifies     |
|-------|------------------|-----------------------------------------|--------------------|--------------|
| MP-01 | default: empty   | default:"Imported", when:"empty"        | Writes “Imported”  | FR-4.2       |
| MP-02 | default: always  | when:"always"                           | Always writes      | FR-4.2       |
| MP-03 | when: never      | when:"never" with default               | Ignores default    | FR-4.2       |
| MP-04 | mapOnly yes      | mapOnly=Yes + extra unmapped fields     | Only mapped change | FR-4.3       |
| MP-05 | dest field miss  | Map to non-existent dest field          | Warning            | FR-4.4, FR-13.2 |

### F) Transforms & Field Types

| ID    | Case                | Inputs                      | Expected                         | Verifies       |
|-------|---------------------|-----------------------------|-----------------------------------|----------------|
| TF-01 | ensureUser single   | Map email → Person           | Person set                        | FR-5.1, FR-9.1 |
| TF-02 | ensureUser multi    | Emails array → PersonMulti   | All resolve; multi IDs written    | FR-5.1, FR-9.2 |
| TF-03 | ensureUser fail     | Bad email                    | Field skipped; warning            | FR-13.2        |
| TF-04 | lookup by ID        | Provide 42                   | Writes lookup                     | FR-9.3         |
| TF-05 | lookup by text      | lookupByText → “Vendor A”    | Resolves to ID; writes            | FR-5.4, FR-9.3 |
| TF-06 | lookup ambiguous    | Two “Vendor A” rows          | Warn; choose first                | FR-5.4, FR-9.4 |
| TF-07 | lookup multi array  | ["Vendor A","Vendor B"]      | Resolves both; writes             | FR-9.4         |
| TF-08 | choice single       | “Approved”                   | Writes                            | FR-9.5         |
| TF-09 | choice multi        | ["High","Low"]               | Writes both                       | FR-9.6         |
| TF-10 | toUTC               | Local date                   | ISO-8601 Z written                | FR-5.2, FR-9.7 |
| TF-11 | stripHTML           | `<p>Hello</p>`               | Hello                             | FR-5.3         |
| TF-12 | URL                 | `https://..., Label`         | Correct format in list            | FR-9.8         |

### G) Error Handling & Resilience

| ID    | Case                  | Inputs                 | Expected                   | Verifies                |
|-------|-----------------------|------------------------|----------------------------|-------------------------|
| ER-01 | Invalid settings JSON | Broken JSON            | Fail-fast parse error      | FR-2.2, FR-13.1         |
| ER-02 | Missing list          | Bad destListName       | Fail-fast list not found   | FR-2.3, FR-13.1         |
| ER-03 | 429 retry             | Throttling simulation  | Retry then success/fail    | NFR-R1                  |
| ER-04 | Field type mismatch   | Send text to Number    | Warn; others proceed       | FR-13.2                 |
| ER-05 | Attachment error      | One bad file           | Warning; run continues     | FR-8.*, FR-13.2         |

---

## 6.5 Performance Checks (NFRs)

| ID    | Scenario                  | Metric target                         | How to measure                | Verifies   |
|-------|---------------------------|----------------------------------------|--------------------------------|------------|
| PF-01 | Single upsert, no attach   | p50 ≤ 5s, p95 ≤ 10s                     | Flow run timestamps            | NFR-P1     |
| PF-02 | 10 attachments ≤25MB total| +≤20s p95                              | Measure attachment step        | NFR-P2     |
| PF-03 | Bulk 100 items             | ≤0.8s/item p50, ≤1.5s/item p95         | Total / count                  | NFR-P3     |
| PF-04 | 3 transforms/field         | ≤30% overhead p95                      | Compare with/without transforms| NFR-P4     |

---

## 6.6 Test Data Seeds
- **Departments**: ["HR","Finance","Ops"]
- **Vendors**: 
  - Title: ["Vendor A","Vendor B"]
  - VendorCode: ["VA","VB"] (two “Vendor A” for ambiguity tests)
- **Tasks (source)**:
  - Task-001: OwnerEmail valid; Tags ["High","Low"]; Dept "HR"; Attach: A.txt, B.png
  - Task-002: OwnerEmail invalid; Dept "Unknown"
  - Task-003: No attach; DueDate local string

---

## 6.7 Execution Notes
- **Reset step**: Optional subflow to wipe dest lists or re-import seeds.
- **Variable naming**: Prefix with `tp_` for test params.
- **Outputs capture**: Store output JSON in a “Test Runs” list with TestId, Pass/Fail, Notes.

---

## 6.8 Pass/Fail Criteria
- **Functional**: All SMK and OP/AM/BK/AT/MP/TF/ER cases pass; failures include reproducible run link/logs.
- **Performance**: PF targets met or explained.
- **Regression**: SMK + rotating subset of cases pass on later builds.

---

## 6.9 Risks & Mitigations
- **Throttling**: Delay 250–500 ms between bulk updates; run off-hours.
- **Directory lag**: Retry ensureUser once before warning.
- **Lookup collisions**: Data includes collision; ensure warnings clear.

---

## 6.10 Deliverables
- Filled Field Catalogs (#4.3) per list.
- Seed scripts (CSV or small PowerShell) for data reset.
- Test Runs SharePoint list capturing outputs/verdicts.
- Short README on suite execution.


### Update: New test cases for retry on 429/5xx, WARN vs FATAL errors, attachment cap behavior.
