
# 17-stage-1-input-validation.md

**Status:** As-built ✅  
**Version:** 1.0  
**Scope:** Stage 1 (Input Validation, Resolve, Normalize, JSON precheck, early‑exit wiring) for the SharePoint item copy flow.  
**Decision summary:**  
- `StartedAt` and `EndedAt` live in **Output.Metrics** (not `Run`).  
- `EndedAt` is set **once** per run; patchers treat a pre‑existing timestamp as authoritative.  
- Keep one source of truth for timestamps → Metrics owns both and computes `DurationMs`.  
- Use kebab‑case for action names and document titles.  

---

## 1) Objectives & Outcomes

Stage 1 guarantees we have a safe, typed, and coherent context **before** any side‑effects. It:

1. Initializes `v-Context` (contract shell).
2. Stamps **Run** metadata (`RunId`, `Flow`, `Environment`) and `Output.Metrics.StartedAt`.
3. Pulls inputs from the **manual trigger**, then **resolves** precedence: `Settings` ⟶ `TriggerValues`.
4. **Normalizes** types/casing/whitespace.
5. **Validates** required fields, enums, and cross‑field rules; accumulates **Errors** and **Warnings**.
6. Drives an **early‑fail gate** that returns the contract when invalid; otherwise continues to Stage 2.
7. Patches **Metrics**: sets `EndedAt` and `DurationMs` when we exit Stage 1 due to validation or precheck failure. (Final end‑of‑flow will patch again if later stages add work.)

**No network calls** or SharePoint mutations occur in Stage 1.

---

## 2) Contract (as used by Stage 1)

Only the relevant parts are shown.

```json
v-Context: {
  "Version": "1.0",
  "Run": { "RunId": "", "Flow": "", "Environment": "" },
  "TriggerValues": {
    "Source": {"SiteUrl": "", "ListName": "", "ItemId": 0},
    "Dest":   {"SiteUrl": "", "ListName": ""},
    "QuickMatch": {"Column": "", "Value": ""},
    "Filter": {"Type": "", "Text": ""},
    "OperationMode": "",          // Create|Update|Upsert (button UI)
    "AttachmentMode": "",         // None|Append|Overwrite|Replace (button UI)
    "Map": "", "MapOnly": false, "Settings": {}, "Bulk": false
  },
  "Settings": { /* resolved + normalized clone of the items above */ },
  "Output": {
    "MatchedIds": [], "CreatedIds": [], "UpdatedIds": [],
    "FieldWarnings": [], "Warnings": [], "Errors": [],
    "AttachmentSummary": {"Added":0,"Overwritten":0,"Replaced":0,"Skipped":0},
    "Log": {"Info": [], "Warn": [], "Error": []},
    "Metrics": {"ApiCalls":0,"Retries":0,"BackoffMsTotal":0,"StartedAt":"","EndedAt":"","DurationMs":0}
  }
}
```

---

## 3) Trigger schema (button)

Button fields (as‑built): `text` (source site), `text_1` (source list), `text_2` (source item id), `text_3` (dest site), `text_4` (dest list), `text_5` (operation), `text_10` (attachment mode), `text_11`/`text_8` (quick‑match column/value), `text_9` (filter type), `text_12` (filter text), `text_7` (map JSON), `boolean` (map only), `text_6` (settings JSON), `boolean_1` (bulk). Stage 1 reads these into `TriggerValues` (see the flow’s **C-InputFromTrigger** compose).

---

## 4) Precedence & Normalization

### Precedence
- **Resolve** step (`S-Resolve`): `Settings` ← `TriggerValues`. For each field, if `Settings.*` is non‑null/non‑empty, it wins; otherwise the `TriggerValues.*` value is used.

### Normalization
- Trimming: strings are trimmed; empty strings become `""` (still considered “missing” by validators when required).
- Casing: `OperationMode`, `AttachmentMode`, and `Filter.Type` are lower‑cased for validation.
- Booleans: `Bulk` and `MapOnly` coerced with `bool(...)` and default to `false` when null.
- Numbers: `Source.ItemId` coerced to `int` when provided (must be `>= 0`).
- `Options`: defaults to `{"About":{"Version":"1.0"}}` when null.
- `Map`: kept as a **string** in `Settings.Map`; parsed to JSON later as `C-ParseTrigMap` → promoted with `C-Promote-MapParsed`.

---

## 5) Validation Rules (as‑built)

Each rule appends a string to `Output.Errors` when violated:

1. Missing: `Settings.Source.SiteUrl`, `Settings.Source.ListName`, `Settings.Dest.SiteUrl`, `Settings.Dest.ListName`.
2. URLs must begin with `https://` when provided.
3. `Settings.OperationMode ∈ {create, update, upsert}`.
4. `Settings.AttachmentMode ∈ {none, append, overwrite, replace}`.
5. If `Settings.Source.ItemId` is present → must be `>= 0`.
6. `Settings.Map` must be present and non‑empty (a JSON string is expected; parsed separately).
7. `Settings.Filter.Type ∈ {odata, caml xml, caml text}` when provided.
8. When `Filter.Type == 'odata'` → `Filter.Text` is required.
9. When `Filter.Type == 'caml xml'` → `Filter.Text` must include a `<View>…</View>` wrapper.
10. When `Filter.Type == 'caml text'` → `Filter.Text` must be a WHERE fragment **without** `<` or `>`.
11. `QuickMatch` requires **both** `Column` and `Value` (or neither).

**Warnings (as‑built):**  
- Large map length threshold: **> 20,000 chars** ⇒ one advisory message in `Output.Warnings`.

---

## 6) Early‑exit gates

- **A-Validate-HasErrors**: If any validation errors exist, Stage 1 patches arrays and metrics, saves `v-Context`, and short‑circuits the branch.
- **A-Exit-HasErrors**: Single exit route to **S-EarlyFail**. It patches arrays & metrics, sets `v-Context`, returns `R-Invalid-Input` (HTTP 200 body with the contract), then terminates with a 400 message pointer to `Output.Errors`.

---

## 7) Action map (what each box owns)

- **V-Init-v-Context** – init contract shell including `Output.Metrics.StartedAt` placeholder.
- **C-RunMeta** – stamps `Run.RunId`, `Run.Flow`, `Run.Environment`; sets `Output.Metrics.StartedAt` if empty.
- **S-JSON-Precheck** – pull trigger values → `TriggerValues`, set variable, and early‑fail on JSON parse errors.
- **S-Stage1-InputValidation** – wrapper scope for resolve, normalize, validate, gating.
  - **S-Resolve** → **C-Settings-Resolve** → **C-Set-Resolve** → **Set-v-Context-Resolve**.
  - **S-Normalize** → **C-Settings-Normalize** → **C-Set-Normalize** → **Set-v-Context-Settings-Normalized**.
  - **S-Validate**
    - **C-Val-Errors** / **C-Val-Warnings** (computes arrays).
    - **A-Validate-HasErrors** → patches arrays/metrics then sets `v-Context`.
    - **C-ParseTrigMap** / **C-Promote-MapParsed** / **Set-v-Context-Settings-Map** (Map promotion).
- **A-Exit-HasErrors** → **S-EarlyFail** → patches arrays/metrics, response, terminate.
- **S-Stage2-FetchMetadata** – placeholder; Stage 1 completes before this.

---

## 8) Expressions pack (copy/paste — as‑built)

### Promote parsed Map
**C-Promote-MapParsed.inputs**
```txt
@{setProperty(
  variables('v-Context'),
  'Settings',
  setProperty(
    variables('v-Context')?['Settings'],
    'Map',
    outputs('C-ParseTrigMap') 
  )
)}
```

**Set-v-Context-Settings-Map.value**
```txt
@json(outputs('C-Promote-MapParsed'))
```

### Patch arrays when validation fails
**C-Output-PatchArrays-Validate.inputs**
```txt
@setProperty(
 variables('v-Context'),
 'Output',
 setProperty(
  setProperty(
   setProperty(
    coalesce(variables('v-Context')?['Output'], json('{}')),
    'Errors',
    union(
      coalesce(variables('v-Context')?['Output']?['Errors'], json('[]')),
      coalesce(outputs('C-Val-Errors'), json('[]')),
      coalesce(variables('v-Errors'), json('[]'))
    )
  ),
  'Warnings',
  union(
    coalesce(variables('v-Context')?['Output']?['Warnings'], json('[]')),
    coalesce(variables('v-Warnings'), json('[]')),
    coalesce(outputs('C-Val-Warnings'), json('[]'))
  )
 ),
 'FieldWarnings',
 union(
   coalesce(variables('v-Context')?['Output']?['FieldWarnings'], json('[]')),
   coalesce(variables('v-FieldWarnings'), json('[]'))
 )
 )
)
```

### Patch metrics when validation fails (set EndedAt once; compute DurationMs)
**C-Output-PatchMetrics-Validate.inputs**
```txt
@setProperty(
  variables('v-Context'),
  'Output',
  setProperty(
    coalesce(variables('v-Context')?['Output'], json('{}')),
    'Metrics',
    setProperty(
      setProperty(
        coalesce(variables('v-Context')?['Output']?['Metrics'], json('{}')),
        'EndedAt',
        coalesce(
          if(
            or(
              equals(variables('v-Context')?['Output']?['Metrics']?['EndedAt'], ''),
              contains(string(variables('v-Context')?['Output']?['Metrics']?['EndedAt']), '@{')
            ),
            null,
            variables('v-Context')?['Output']?['Metrics']?['EndedAt']
          ),
          utcNow()
        )
      ),
      'DurationMs',
      div(
        sub(
          ticks(
            coalesce(
              if(
                or(
                  equals(variables('v-Context')?['Output']?['Metrics']?['EndedAt'], ''),
                  contains(string(variables('v-Context')?['Output']?['Metrics']?['EndedAt']), '@{')
                ),
                null,
                variables('v-Context')?['Output']?['Metrics']?['EndedAt']
              ),
              utcNow()
            )
          ),
          ticks(
            coalesce(
              if(
                or(
                  equals(variables('v-Context')?['Output']?['Metrics']?['StartedAt'], ''),
                  contains(string(variables('v-Context')?['Output']?['Metrics']?['StartedAt']), '@{')
                ),
                null,
                variables('v-Context')?['Output']?['Metrics']?['StartedAt']
              ),
              utcNow()
            )
          )
        ),
        10000
      )
    )
  )
)
```

### Early‑fail patchers (same semantics)
- **C-Output-PatchArrays.inputs** — same shape as the Validate variant but without `outputs('C-Val-Warnings')` in the warnings union.
- **C-Output-PatchMetrics.inputs** — same as `C-Output-PatchMetrics-Validate`.

### Run metadata + StartedAt
**C-RunMeta.inputs**
```txt
@setProperty(
 setProperty(
  variables('v-Context'),
  'Run',
  setProperty(
   setProperty(
    setProperty(
     coalesce(variables('v-Context')?['Run'], json('{}')),
     'RunId', coalesce(workflow()?['run']?['name'], workflow()?['run']?['id'], guid())
   ),
   'Flow', coalesce(workflow()?['name'], '')
  ),
  'Environment', coalesce(workflow()?['tags']?['environmentName'], workflow()?['tags']?['environment'], '')
 )
 ),
 'Output',
 setProperty(
  coalesce(variables('v-Context')?['Output'], json('{}')),
  'Metrics',
  setProperty(
   coalesce(variables('v-Context')?['Output']?['Metrics'], json('{}')),
   'StartedAt', coalesce(variables('v-Context')?['Output']?['Metrics']?['StartedAt'], utcNow())
  )
 )
)
```

---

## 9) What the last run tells us

From your latest run (Sep 2), Stage 1 behaved as intended:
- `Run` metadata populated (`RunId`, `Flow`, `Environment`).  
- `Output.Metrics` shows `StartedAt`, `EndedAt`, and `DurationMs` (~1009 ms).  
- No **Errors** or **Warnings** because inputs were empty/neutral and Stage 1 didn’t reach any side‑effect stage.  
- `Settings.Map` contained a newline (the button’s Map field was blank), which is acceptable; promotion logic keeps `null`/blank until you provide JSON.  

---

## 10) Acceptance checklist (Stage 1 = ✅ when all pass)

- [ ] Empty trigger values produce the 4 “Missing Settings.…Site/List” errors.  
- [ ] `OperationMode`/`AttachmentMode` enums are enforced (case‑insensitive on input).  
- [ ] QuickMatch both‑or‑neither rule enforced.  
- [ ] Filter rules enforced for each Type.  
- [ ] `EndedAt` set at the validation/early‑fail gate and **never overwritten** later in Stage 1.  
- [ ] `DurationMs` = (`EndedAt` – `StartedAt`) using engine ticks/10000.  
- [ ] Response on early‑fail returns the whole contract (see **R-Invalid-Input**).  

---

## 11) Open items & next steps

- Stage 2 (Fetch Metadata): query list schemas and cache into `Data.SrcListMeta`, `Data.DestListMeta`, `Data.DestFields`.  
- Stage 3–4: read source item + attachments, then transform according to `Settings.Map`.  
- Stage 7: write results and patch `CreatedIds` / `UpdatedIds`, attachment summary, and final metrics.

