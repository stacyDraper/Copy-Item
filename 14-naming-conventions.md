# 14-naming-conventions.md

**Purpose:**  
Establish a single, project-wide standard for naming variables, actions, and components in Power Automate flows to maximize clarity, consistency, and maintainability.  
These conventions apply to *all stages* of the Copy-Item workflow.

---

## 1. Guiding Principles
- **Clarity over brevity:** Short prefixes are fine, but not at the cost of readability.
- **Consistency beats preference:** One style for all stages and all flow authors.
- **What you see is what you type:** The action title and the reference name in expressions must match exactly.
- **Scan-friendly runs:** Prefixes group similar actions together in the run history for easy troubleshooting.
- **Avoid invisible characters:** Underscores `_` are harder to see in the designer; use dashes `-` in all titles and names.

---

## 2. Casing Rules
We use **CamelCase after the prefix** for all semantic parts:
- First letter of each semantic word is capitalized.
- Acronyms follow the **Acronym Rule** below.
- Examples:  
  - ✅ `v-SrcSiteUrl`  
  - ✅ `H-GET-DestFields`  
  - ✅ `PJ-ParseJson`  

---

## 3. Acronym Rule
**Purpose:** Keep names readable while preserving recognizability of common acronyms.

| Acronym Length | Rule | Examples |
|----------------|------|----------|
| ≤ 3 letters | ALL CAPS | `URL`, `ID`, `API`, `SKU` → `v-SrcSiteURL`, `v-DestListID` |
| ≥ 4 letters | Capitalize first letter only | `Json`, `Oauth`, `Ascii` → `PJ-ParseJson`, `v-OauthToken` |

**Examples in practice:**  
- ✅ `H-GET-SrcSiteURL` *(3-letter acronym in all caps)*  
- ✅ `PJ-ParseJson` *(4-letter acronym with only first letter capitalized)*  
- ❌ `v-srcsiteurl` *(all lowercase — hard to read)*  
- ❌ `PJ-ParseJSON` *(long acronym fully capitalized — visual clutter)*  

---

## 4. Prefix Standards
| Prefix | Action Type | Example | Notes |
|--------|-------------|---------|-------|
| **S-** | Scope | `S-Stage1-InputValidation` | Stage number + purpose. |
| **v-** | Variable (init/set) | `v-Settings` | Lowercase `v-` followed by semantic name. |
| **C-** | Compose | `C-BuildFormValues` | CamelCase semantic name. |
| **H-<VERB>-** | HTTP Request | `H-GET-SrcItem` | Use HTTP verb in ALL CAPS. |
| **PJ-** | Parse JSON | `PJ-ParseSettings` | Always verb-noun. |
| **A-** | Generic Action / Condition / Switch | `A-ValidateMap` | Only if no other prefix applies. |

---

## 5. Variable Naming
- **Prefix:** `v-`
- **Format:** `v-<SemanticCamel>`
- **Apply Acronym Rule** for any acronyms in the name.
- Examples:  
  - `v-Settings`  
  - `v-Map`  
  - `v-SrcItemId`  
  - `v-SrcSiteURL`  
  - `v-CreatedIds`  
  - `v-AttachmentSummary`

**Expression use:**  
```plaintext
variables('v-Settings')
coalesce(variables('v-SrcItemId'), 0)
```

---

## 6. Compose Naming
- **Prefix:** `C-`
- **Format:** `C-<ActionPurpose>`
- Apply Acronym Rule where relevant.
- Examples:  
  - `C-DefaultSettings`
  - `C-FilterEditable`
  - `C-BuildFormValues`

**Expression use:**  
```plaintext
outputs('C-BuildFormValues')
```

---

## 7. HTTP Naming
- **Prefix:** `H-<VERB>-<Purpose>`
- HTTP verb in all caps: `GET`, `POST`, `PATCH`, `DELETE`.
- Semantic part in CamelCase.
- Examples:  
  - `H-GET-SrcItem`
  - `H-POST-Create`
  - `H-POST-VULI-Update`

---

## 8. Parse JSON Naming
- **Prefix:** `PJ-`
- **Format:** `PJ-<Verb><Object>`
- Examples:  
  - `PJ-ParseSettings`
  - `PJ-ParseMap`

---

## 9. Generic Actions
- **Prefix:** `A-`
- **Format:** `A-<Verb><Object>`
- Examples:  
  - `A-ResolveSrcId`
  - `A-BulkGuard`
  - `A-AppendWarning`

---

## 10. Test Parameter Naming
- **Prefix:** `tp-`
- **Format:** `tp-<SemanticCamel>`
- Apply Acronym Rule where relevant.
- Examples:  
  - `tp-DestListName`  
  - `tp-APIKey`

---

## 11. Special Notes
- **Case sensitivity:** Power Automate expression references are case-insensitive, but action titles must always follow these rules for consistency.
- **Migration from underscores:** Old names like `v_srcItem` should be renamed in both title and references to `v-SrcItem`.
- **Bulk renaming:** After renaming, recheck manually typed expressions to ensure no broken references.

---

## 12. Quick Reference Table
| Element | Prefix | Example | Casing |
|---------|--------|---------|--------|
| Scope | `S-` | `S-Stage4-Matching` | Pascal after stage |
| Variable | `v-` | `v-MatchedIds` | Camel after dash |
| Compose | `C-` | `C-BuildFormValues` | Camel after dash |
| HTTP | `H-<VERB>-` | `H-GET-DestFields` | Verb caps, then Camel |
| Parse JSON | `PJ-` | `PJ-ParseMap` | Camel after dash |
| Generic | `A-` | `A-BulkGuard` | Camel after dash |
| Test Param | `tp-` | `tp-DestListName` | Camel after dash |
