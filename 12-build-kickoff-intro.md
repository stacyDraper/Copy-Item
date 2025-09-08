# Build Kickoff — Intro Prompt & Working Conventions

This page gives you: (1) a **ready-to-paste prompt** to use with ChatGPT while we build the flow step‑by‑step, and (2) the **conventions** we’ll follow in Power Automate so every action is predictable and debuggable.

---

## 1) Paste‑This Intro Prompt (to start build sessions)

> **Copy & paste into a new chat when you want me to drive the next build step:**
>
> **Context:** We’re building the “Copy‑Item” Power Automate flow for SharePoint Online. MVP features are fixed per our docs. Use the established inputs (`sourceSiteUrl`, `sourceListName`, `destSiteUrl`, `destListName`, `sourceItemId`, `map`, `operation`, `destMatchColumn`, `destMatchValue`, `attachmentMode`, `mapOnly`, `settings`). Field types include People/Lookup/Choice single & multi. Writes use ValidateUpdateListItem. Matching supports quick match and `settings.match` (simple/odata/caml). Attachments support none/append/overwrite/replace. Output is the structured JSON contract.
>
> **What I want now:** Walk me through building the **next action(s)** in the flow with exact details: the **action type**, **name**, **inputs**, **headers/body**, **expressions**, **variables used**, **expected outputs**, and **error handling** (including scopes/conditions). Use our naming conventions and variable schema below. Assume dynamic columns and runtime mapping. Provide copy‑ready payloads and expressions.
>
> **Conventions available:** See the naming, variables, scopes, and helper expressions below and refer back to them.
>
> Then propose the exact actions to add and the order to add them. When I say “go,” give me the literal payloads and expressions to paste.

---

## 2) Naming Conventions (Power Automate)

- **Actions:** `A_<Stage>_<Verb>_<N>` (e.g., `A_Validate_ParseMap_01`)
- **Scopes:** `S_<Stage>_<Name>` (e.g., `S_Stage1_InputValidation`)
- **Variables (Initialize/Set):** `v_<camelCase>` (e.g., `v_srcItem`, `v_destFields`)
- **Compose:** `C_<Purpose>` (e.g., `C_DefaultSettings`)
- **HTTP to SPO:** `H_<Verb>_<Purpose>` (e.g., `H_GET_SrcItem`, `H_POST_VULI_Update`)

---

## 3) Core Variables (create early)

| Name | Type | Purpose |
|---|---|---|
| `v_settings` | Object | Parsed `settings` or default. |
| `v_map` | Array | Parsed `map`. |
| `v_srcItemId` | Integer | Final source item id (from input or context). |
| `v_srcItem` | Object | Source item JSON (expanded if needed). |
| `v_destFields` | Array | Destination fields schema. |
| `v_matchedIds` | Array | IDs matched for update path. |
| `v_createdIds` | Array | IDs created. |
| `v_updatedIds` | Array | IDs updated. |
| `v_warnings` | Array | Warning strings. |
| `v_fieldWarnings` | Array | Objects `{field, message}`. |
| `v_errors` | Array | Error strings. |
| `v_attachmentSummary` | Object | `{ mode, added, overwritten, replaced, skipped }`. |

> Initialize arrays/objects with `[]`/`{}`; keep `v_attachmentSummary` seeded to `{ "mode": "none", "added":0, "overwritten":0, "replaced":0, "skipped":0 }` and update later.

---

## 4) Standard Headers

- **Accept:** `application/json;odata=nometadata`
- **Content-Type:** `application/json;odata=verbose` (for VULI/CAML posts)

---

## 5) Helper Expressions (copy‑ready)

- **Coalesce object property:**  
  `if(equals(variables('v_tmp'), null), <fallback>, variables('v_tmp'))`
- **Is null/empty string:**  
  `or(equals(<x>, null), equals(string(<x>), ''))`
- **Append string warning:**  
  `concat(<prefix>, ': ', <detail>)`
- **Ensure array from value:**  
  `if(equals(typeOf(<x>), 'Array'), <x>, createArray(<x>))`
- **Build `;#` multi‑ID string from array of numbers:**  
  `concat(';#', join(<idArray>, ';#'), ';#')`

---

## 6) Control Patterns

- **Fail‑fast**: Place input parsing in `S_Stage1_InputValidation`. On failure, add to `v_errors` and **Terminate** with `Failed`.
- **Warn & continue**: For per‑field issues, append to `v_fieldWarnings` and continue the item.
- **Retry**: Use HTTP action retry policy (Exponential, min 1s, max 30s, count 3). Respect `Retry-After`.

---

## 7) Ready Phrases For You To Say

- “**Go**: Build Stage 1 (Input Validation): initialize variables, parse `map`/`settings`, and compute `v_srcItemId` from context.”  
- “**Go**: Build Stage 2 (Get Source Item): add GET action with `$expand=AttachmentFiles` when needed.”  
- “**Go**: Build Stage 3 (Get Destination Fields): fetch `/fields` and filter editable.”  
- “**Go**: Build Stage 4 (Match): quick match vs `settings.match`, OData vs CAML.”  
- “**Go**: Build Stage 5 (Write): create/validateUpdateListItem, bulk loop.”  
- “**Go**: Build Stage 6 (Attachments): append/overwrite/replace logic.”  
- “**Go**: Build Stage 7 (Assemble Output): compose the final JSON.”

---

**When you’re ready, tell me “Go: Stage 1,” and I’ll return copy‑paste actions with exact payloads and expressions.**


### Update: Stage outline corrected to 1–7 flow (Stage 5 = Write, Stage 6 = Attachments, Stage 7 = Outputs).
