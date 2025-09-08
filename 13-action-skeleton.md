# Action‑by‑Action Skeleton — Copy‑Item Flow (MVP)

This is the concise scaffold we’ll fill in during build sessions. Each stage lists: **actions to add**, **names**, **inputs**, and **expected outputs**.

---

## S_Stage1_InputValidation

**Actions**
1) **Initialize Variables**: all core variables from the kickoff doc.  
2) **C_DefaultSettings (Compose)**: JSON for default settings.  
3) **A_Validate_ParseSettings (Parse JSON)**: from trigger `settings` or default.  
4) **A_Validate_ParseMap (Parse JSON)**: from trigger `map`.  
5) **A_Validate_ResolveSrcId (Compose)**: resolve `v_srcItemId` from trigger or selected-item context.  
6) **Condition**: required inputs present; otherwise append error and **Terminate (Failed)**.

**Outputs**
- `v_settings`, `v_map`, `v_srcItemId` set and valid.

---

## S_Stage2_SourceItem

**Actions**
1) **H_GET_SrcItem (HTTP)**: GET source item with `$select=*` and optional `$expand=AttachmentFiles,FieldValuesAsText`.  
2) **Set v_srcItem (Set variable)**.

**Outputs**
- `v_srcItem` with field data and (optionally) attachments metadata.

---

## S_Stage3_DestSchema

**Actions**
1) **H_GET_DestFields (HTTP)**: GET `/fields?$select=InternalName,TypeAsString,ReadOnlyField,Hidden,LookupList,LookupField,AllowMultipleValues`.  
2) **C_FilterEditable (Compose)**: filter editable fields.  
3) **Set v_destFields**.

**Outputs**
- `v_destFields` filtered to editable, visible fields.

---

## S_Stage4_Matching

**Actions**
1) **C_BuildQuickMatch (Compose)**: if `destMatchColumn` + `destMatchValue`, synthesize simple criteria.  
2) **Condition**: prefer `settings.match` if present; else quick.  
3) **H_GET_Match_OData or H_POST_Match_CAML (HTTP)** depending on mode.  
4) **C_ExtractIds (Compose)** → `v_matchedIds`.  
5) **Bulk Guard**: if `bulk=true` and `length(v_matchedIds) > 1000` and env not set → **Terminate (Failed)**.

**Outputs**
- `v_matchedIds` (array).

---


## S_Stage5_Write

> One stage containing sub‑scopes 5A–5F. Build form values once, then route to the correct writer based on **source/dest type** and **operation**. Each sub‑scope ends with a single commit to `v-Context`.

### S-5A-Build-FormValues
**Actions**
1. **C-5A-ValidateMap** (Compose) – warn for hidden/readonly fields in `v-Context.map` and missing source fields.
2. **C-5A-ApplyTransforms** (Compose) – use Transform Catalog to coerce values.
3. **C-5A-BuildFormValues** (Compose) – produce `[{ "FieldName": "<InternalName>", "FieldValue": <value> }, ...]`.
4. **Set variable – v-Context** (commit) – set `data.formValues` and append `output.fieldWarnings`.

**Outputs**
- `v-Context.data.formValues`

---

### S-5B-Decide-WriteMode
**Actions**
1. **C-5B-IsSourceDocLib** – from `data.srcListMeta`.
2. **C-5B-IsDestDocLib** – from `data.destListMeta`.
3. **C-5B-Op** – `create|update|upsert` from settings.
4. **Switch / Condition** → Doc→Doc (5C), List→List (5D), List→Doc (5E), Doc→List (5F).

---

### S-5C-Write-DocToDoc (like‑kind)
**Create**
- **H-5C-UploadFile**: `POST /_api/web/GetFolderByServerRelativePath(decodedurl='{destFolder}')/Files/add(url='{filename}',overwrite=@{equals(variables('v-Context')?['settings']?['attachmentMode'],'overwrite')})`
- **H-5C-UpdateMetadata**: `POST /_api/web/GetFileByServerRelativePath(decodedurl='{destFolder}/{filename}')/ListItemAllFields` body from `data.formValues`.
**Update/Upsert**
- For each matched ID → upload (overwrite policy) then update metadata.

**Commit**
- Append created/updated IDs, warnings for collisions; bump `metrics.apiCalls`.

---

### S-5D-Write-ListToList (like‑kind)
**Create**
- **H-5D-CreateItem**: `POST /_api/web/lists/getbytitle('{destList}')/items` with `data.formValues`.
**Update/Upsert**
- **H-5D-UpdateItem**: `PATCH /_api/web/lists/getbytitle('{destList}')/items({id})` with `data.formValues`.
**Attachments (same‑kind only)**
- Apply `attachmentMode`: append/overwrite/replace via `.../items({id})/AttachmentFiles/add(FileName='{name}')`.

**Commit**
- Append IDs; update `output.attachmentSummary` and `output.fieldWarnings`.

---

### S-5E-Write-ListToDoc (cross‑kind)
**Loop attachments → documents**
1. **H-5E-UploadFile** to dest folder (overwrite per policy).
2. **H-5E-UpdateMetadata** on uploaded file’s `ListItemAllFields` with `data.formValues`.

**Commit**
- Append each file’s ListItem ID to created/updated; compute `output.attachmentSummary`.

---

### S-5F-Write-DocToList (cross‑kind)
**Item write** – create/update list item with `data.formValues`.
**Attach source file** – apply `attachmentMode` using `.../items({id})/AttachmentFiles/add(FileName='{sourceFileName}')`.

**Commit**
- Set item ID; update `output.attachmentSummary`.


## S_Stage6_AssembleOutput

**Actions**
1. **C-6-Metrics-End** (Compose) – end time + duration:  
   - `endedAt = utcNow()`  
   - `durationMs = sub(ticks(utcNow()), ticks(variables('v-Context')?['metrics']?['startedAt']))`
2. **Set variable – v-Context** (commit) – stamp `metrics.endedAt` & `metrics.durationMs`.
3. **C-6-ResponseBody** (Compose) – final contract pulling from `v-Context.output`:
   ```json
   {
     "operation": "@{variables('v-Context')?['settings']?['operation']}",
     "matchedCount": "@{length(coalesce(variables('v-Context')?['output']?['matchedIds'], createArray()))}",
     "createdIds": "@{variables('v-Context')?['output']?['createdIds']}",
     "updatedIds": "@{variables('v-Context')?['output']?['updatedIds']}",
     "warnings": "@{variables('v-Context')?['output']?['warnings']}",
     "errors": "@{variables('v-Context')?['output']?['errors']}",
     "attachmentSummary": "@{variables('v-Context')?['output']?['attachmentSummary']}"
   }
   ```
4. **Response – R-200** – return `outputs('C-6-ResponseBody')`.

**Notes**
- Keep Stage 6 free of side effects (read‑only assembly).
- If you log to a run‑history list, add a scoped action here that is tolerant to failures.

## S_Stage7_Output

**Actions**
1) **C_Output (Compose)**: build the final JSON using the Output schema.  
2) **Respond (HTTP Response or Return)**.  
3) **Optional**: write a summary row to `COPYITEM_RUNLOG_LIST` if env is present.

**Outputs**
- Final contract emitted to caller.
