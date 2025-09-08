# 9) Transform Catalog (MVP)

Transforms run left → right in the transform list.  
If any transform fails, that field is skipped and a warning is logged; the rest of the item continues (per FR-13.2).  
Multi-value inputs (arrays) are handled by mapping the transform over each element unless stated otherwise.

**Common helpers:**

- **isEmpty(x):** `x === null || x === "" || (Array.isArray(x) && x.length===0)`  
- **toArray(x):** wraps non-array as `[x]`  
- **SP multi-ID format:** `;#<id1>;#<id2>;#` (for PersonMulti / LookupMulti)  
- **SP multi-choice format:** `;#<val1>;#<val2>;#`  

---

## T-01 ensureUser

**Purpose:** Convert a person identifier (email/UPN/login) into a SharePoint User ID suitable for Person fields.

**Input → Output**

- Input: string (email/UPN) or array of strings  
- Output (single): user ID as string (e.g., `"23"`)  
- Output (multi): SP multi-ID string `;#23;#45;#`

**Algorithm**

1. For each input identity:  
   - POST `/_api/web/ensureuser` with `{ "logonName": <identity> }`  
   - Read `d.Id` (or `Id`) from the response.  
2. Compose output:  
   - Single: `"23"`  
   - Multi: `;#23;#45;#`  

**Edge Cases**

- Not found/guest blocked → log warning and skip that identity. If none left, skip field.  
- Mixed valid/invalid in multi: write only valid ones, warn with counts.

**Examples**

- `"jane@contoso.com"` → `"42"`  
- `["jane@contoso.com","bad@x"]` → `;#42;#` + warn `"1 user not found"`

**SP Formatting**

- Person (single): `"42"`  
- Person (multi): `;#42;#17;#`

---

## T-02 lookupByText

**Purpose:** Resolve Lookup display text(s) to ID(s) using the destination field’s LookupList + LookupField.

**Input → Output**

- Input: string (display text) or array of strings  
- Output (single): `"ID"` as string  
- Output (multi): `;#ID;#ID;#`

**Algorithm**

1. From destination field metadata, get `LookupListGuid` + `LookupField`.  
2. Query target list:  
   GET `/lists(guid'<guid>')/items?$select=Id,<LookupField>&$filter=<LookupField> eq '<text>'&$top=2`  
3. If exactly one match → take Id.  
   - If 0 → warn `"lookupByText not found: <text>"` (skip that value)  
   - If >1 → warn `"lookupByText ambiguous: <text>"`; take the first.

**Edge Cases**

- Case-insensitive by default in SharePoint.  
- Escape quotes in OData filter.

**Examples**

- `"Vendor A"` → `"37"`  
- `["Vendor A","Vendor B"]` → `;#37;#41;#`  
- Ambiguous `"Vendor A"` → choose first, warn.

**SP Formatting**

- Lookup (single): `"37"`  
- Lookup (multi): `;#37;#41;#`

---

## T-03 toUTC

**Purpose:** Normalize date/time into ISO-8601 UTC for SharePoint DateTime columns.

**Input → Output**

- Input: string date/time or array  
- Output (single): `"YYYY-MM-DDTHH:MM:SSZ"`

**Algorithm**

1. Parse input using culture-invariant parser.  
2. If input has offset → convert to UTC.  
3. If no offset:  
   - Treat as local and log warning (per NFR-I1).  

**Edge Cases**

- Invalid date → warn, skip field.  
- DST handled by parser.

**Examples**

- `"2025-08-14T09:00:00-04:00"` → `"2025-08-14T13:00:00Z"`

**SP Formatting**

- DateTime (single): `"2025-08-14T13:00:00Z"`

---

## T-04 stripHTML

**Purpose:** Remove markup from rich text.

**Algorithm**

- Remove tags, decode HTML entities, collapse whitespace.

**Examples**

- `"<p>Hello <strong>World</strong></p>"` → `"Hello World"`

**SP Formatting**

- Plain string.

---

## T-05 trim

- `"  Alpha  "` → `"Alpha"`

## T-06 lowerCase / upperCase

- `"AbC"` → `"abc"` / `"ABC"`

## T-07 join

- `["High","Low"]` + `join::"; "` → `"High; Low"`

## T-08 split

- `"A,B,C"` + `split::","` → `["A","B","C"]`

## T-09 coalesce

- `"" + coalesce::"Unknown"` → `"Unknown"`

---

## Composition Patterns

- Person single: `["trim","lowerCase","ensureUser"]`  
- Person multi: `["split::","","trim","lowerCase","ensureUser"]`  
- Lookup single: `["trim","lookupByText"]`  
- Multi-choice: typeHint `"ChoiceMulti"`

---

## SharePoint Serialization

| TypeHint       | Format |
|----------------|--------|
| Text / Note    | `"string"` |
| Number / Bool  | `"123.45" / "true"` |
| DateTime       | `"YYYY-MM-DDTHH:MM:SSZ"` |
| Url            | `"https://..., Label"` |
| Choice         | `"Approved"` |
| ChoiceMulti    | `;#High;#Low;#` |
| User           | `"23"` |
| UserMulti      | `;#23;#45;#` |
| Lookup         | `"37"` |
| LookupMulti    | `;#37;#41;#` |

---

## Validation & Warnings

- Field failure → `fieldWarnings[]`  
- Ambiguity → proceed, warn  
- Empty after transform → skip, warn  
- Type mismatch → warn only

---
