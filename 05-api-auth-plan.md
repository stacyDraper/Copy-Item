# Copy-Item Flow — API & Auth Plan (MVP)

## 5.1 Core tech choices

- **Transport:** Power Automate Send an HTTP request to SharePoint (SPO REST).
- **Write method:** Prefer `ValidateUpdateListItem` for field updates (handles complex types consistently). Use REST POST/PATCH for create + simple reads.
- **Match queries:** OData (`?$filter=...`) and CAML (`/GetItems POST`).
- **Attachments:** REST AttachmentFiles endpoints for list items.
- **Identity:** Connection Reference to SharePoint (least privilege).

---

## 5.2 Endpoints (by task)

### A) Read source item

```
GET {sourceSite}/_api/web/lists/getbytitle('{sourceList}')/items({sourceItemId})?$select=*
```

- (If needed) `&$expand=AttachmentFiles,FieldValuesAsText`
- Attachments list:  
  `GET .../items({id})/AttachmentFiles?$select=FileName,ServerRelativeUrl`

### B) Read destination schema (for mapping/type decisions)

```
GET {destSite}/_api/web/lists/getbytitle('{destList}')/fields?$select=InternalName,Title,TypeAsString,ReadOnlyField,Hidden,LookupList,LookupField,AllowMultipleValues
```

### C) Match destination item(s)

- **OData (simple):**  
  `GET {destSite}/_api/web/lists/getbytitle('{destList}')/items?$select=Id&$filter=...&$top={N}`
- **CAML (advanced/large lists):**  
  `POST {destSite}/_api/web/lists/getbytitle('{destList}')/GetItems`  
  **Body:**

```json
{
  "query": {
    "__metadata": { "type": "SP.CamlQuery" },
    "ViewXml": "<View><Query>...Where...</Query><ViewFields><FieldRef Name='ID'/></ViewFields><RowLimit>200</RowLimit></ViewXml>"
  }
}
```

- **Headers:**  
  `accept: application/json;odata=nometadata`  
  `content-type: application/json;odata=verbose`

### D) Create destination item

- Minimal create:  
  `POST {destSite}/_api/web/lists/getbytitle('{destList}')/items`  
  Body can be `{}` or a seed like `{ "Title": "..." }` → returns Id.

### E) Update destination fields (preferred)

`ValidateUpdateListItem` works for single/multi, Person/Lookup/Choice.

- Update existing:  
  `POST {destSite}/_api/web/lists/getbytitle('{destList}')/items({id})/validateupdatelistitem`  
  **Body:**

```json
{
  "formValues": [
    { "FieldName": "Title", "FieldValue": "My Value" },
    { "FieldName": "Owner", "FieldValue": "15" }
  ],
  "bNewDocumentUpdate": false
}
```

- **Headers:** same as above.  
- **Note:** Direct PATCH possible, but VULI is safer.

### F) Attachments (list items)

- Download:  
  `GET .../AttachmentFiles('{fileName}')/$value` (binary)  
- Add:  
  `POST .../AttachmentFiles/add(FileName='{fileName}')` (binary body)  
- List current:  
  `GET .../AttachmentFiles`  
- Delete:  
  `POST .../AttachmentFiles('{fileName}')/recycle()`

### G) Person resolution

```
POST {site}/_api/web/ensureuser
Body: {"logonName": "user@contoso.com"}
```
→ Response includes Id.

### H) Lookup resolution by text (MVP)

1. Get dest field schema (LookupList + LookupField).  
2. Query lookup list by text:  
   `GET {destSite}/_api/web/lists(guid'{LookupListGuid}')/items?$select=Id,{LookupField}&$filter={LookupField} eq '{text}'&$top=2`  
3. Use ID if single match, else warn.

---

## 5.3 Field write rules (with ValidateUpdateListItem)

| SharePoint Type (TypeAsString) | Single value FieldValue            | Multi value FieldValue              |
|--------------------------------|-------------------------------------|--------------------------------------|
| Text / Note                    | "Some text"                        | n/a                                  |
| Number / Currency / Boolean    | "123.45" / "true"                   | n/a                                  |
| DateTime                       | "2025-08-14T15:00:00Z" (use toUTC) | n/a                                  |
| URL                            | "https://contoso.com, Label here"   | n/a                                  |
| Choice                         | "Approved"                         | ";#Approved;#Pending;#"              |
| Person                         | "15" (user ID)                      | ";#15;#27;#"                         |
| Lookup                         | "42" (target item ID)               | ";#42;#73;#"                         |

**Notes:**
- Always send strings for VULI.
- Multi fields: classic `;#`-delimited format.
- Skip read-only/hidden dest fields.

---

## 5.4 Matching rules

### Quick match (trigger fields)

If `operation` in `{update, upsert}` and both `destMatchColumn` & `destMatchValue` provided:

```json
{ "mode": "simple", "criteria": { "<column>": "<value>" }, "bulk": false, "expectation": "single" }
```

Execute as CAML if large list or special chars; else OData.

### settings.match (advanced)

- **simple:** equality / ranges → CAML.  
- **odata:** pass `$filter` directly.  
- **caml:** pass `<View>...</View>` to GetItems.

Bulk: if bulk=true → update all matches. Update-only: fail if no matches.

---

## 5.5 Attachments logic (summary)

- **none:** do nothing.  
- **append:** add missing files.  
- **overwrite:** replace name matches.  
- **replace:** clear all then copy all.  
- File errors → warn, continue.

---

## 5.6 Headers & payload conventions

- **Accept:** `application/json;odata=nometadata`
- **Content-Type:**  
  - JSON: `application/json;odata=verbose`  
  - Binary: none (auto in PA)
- **Auth:** connector-based.

---

## 5.7 Throttling & retries

- Retry Policy: Exponential, 3 retries, min 1s, max 30s.  
- Honor Retry-After.  
- Delay between bulk updates (250–500 ms).  
- Collect failures into warnings/errors.

---

## 5.8 Environment variables

- `COPYITEM_RUNLOG_LIST` — optional log list.  
- `COPYITEM_ALLOW_LARGE_BULK` — `"true"` to allow >1000 matches.

---

## 5.9 Auth & Permissions

- Service account with read (source) + contribute (dest).  
- No site admin needed.  
- If ensureUser blocked, warn and skip.

---

## 5.10 Implementation notes (PA specifics)

- One HTTP connector per site (strict) or tenant-wide (loose).  
- Centralize transform dispatch.  
- Escape XML for CAML.  
- Normalize arrays for multi fields before send.
