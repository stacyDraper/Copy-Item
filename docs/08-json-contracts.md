# Copy-Item Flow — JSON Contracts (MVP)

## 8.1 map (Trigger input: Text/JSON)

### Purpose
Defines how to move/shape values from source item → destination item. Supports defaults, conditional application, transforms, and type hints. Order matters; transforms run left→right.

### JSON Schema (Draft-07)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Field Mapping Array",
  "type": "array",
  "minItems": 1,
  "items": {
    "type": "object",
    "additionalProperties": false,
    "required": ["source", "dest"],
    "properties": {
      "source": { "type": "string", "minLength": 1 },
      "dest":   { "type": "string", "minLength": 1 },
      "default": {
        "type": ["string","number","boolean","null","array","object"]
      },
      "when": {
        "type": "string",
        "enum": ["always", "empty", "never"],
        "default": "empty"
      },
      "transform": {
        "oneOf": [
          { "type": "string", "minLength": 1 },
          {
            "type": "array",
            "minItems": 1,
            "items": { "type": "string", "minLength": 1 }
          }
        ]
      },
      "typeHint": {
        "type": "string",
        "enum": [
          "Text","Note","Number","Currency","Boolean","DateTime",
          "Url",
          "Choice","ChoiceMulti",
          "User","UserMulti",
          "Lookup","LookupMulti"
        ]
      }
    }
  }
}
```

**Allowed transforms (MVP)**  
- ensureUser — email/login → resolves to SP user ID (supports arrays for multi).  
- toUTC — parses a date/time and outputs ISO-8601 Z.  
- stripHTML — removes HTML tags (leaves text).  
- lookupByText — resolves Lookup display text → ID (supports arrays for multi).  

You can add more later without changing this contract.

**Example**
```json
[
  { "source": "Title", "dest": "Title" },
  { "source": "State", "dest": "Status", "default": "Imported", "when": "always" },
  { "source": "AssignedToEmail", "dest": "Owner", "transform": ["trim","lowerCase","ensureUser"], "typeHint": "User" },
  { "source": "TagsArray", "dest": "Tags", "typeHint": "ChoiceMulti" },
  { "source": "VendorNames", "dest": "Vendor", "transform": "lookupByText", "typeHint": "LookupMulti" }
]
```

## 8.2 settings (Trigger input: Text/JSON — optional, advanced)

### Purpose
Holds matching/filtering (and a few advanced options). Casual users can skip this; your quick-match fields populate an internal match when provided. Advanced users paste settings to do OData/CAML or bulk.

### JSON Schema (Draft-07) — MVP subset
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Copy-Item Settings (MVP)",
  "type": "object",
  "additionalProperties": false,
  "required": ["version"],
  "properties": {
    "version": { "type": "string", "pattern": "^\\d+\\.\\d+$" },
    "match": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "mode": { "type": "string", "enum": ["simple","odata","caml"], "default": "simple" },
        "criteria": {},
        "bulk": { "type": "boolean", "default": false },
        "expectation": { "type": "string", "enum": ["single","any","none"], "default": "any" }
      }
    },
    "options": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "confirmBulk": { "type": "boolean", "default": false }
      }
    }
  }
}
```

**Criteria formats**
- mode: “simple” → JSON equality/ranges (converted to CAML)  
  Example: `{"Title":"Widget-123"}`  
  Example: `{"Modified":{"ge":"2025-08-01T00:00:00Z"}}`  
- mode: “odata” → object with $filter (+ optional $top, $orderby)  
  Example: `{ "$filter": "Status eq 'Active' and Category eq 'Hardware'" }`  
- mode: “caml” → string: `<View>...<Query>...</Query>...</View>`

**Examples**  
**A) Quick, safe defaults (no bulk)**
```json
{
  "version": "1.0",
  "match": { "mode": "simple", "criteria": { "$filter": "ID eq -1", "$top": 1 }, "bulk": false, "expectation": "any" }
}
```

**B) Advanced OData with bulk**
```json
{
  "version": "1.0",
  "match": {
    "mode": "odata",
    "criteria": { "$filter": "Status eq 'Active' and Category eq 'Hardware'" },
    "bulk": true,
    "expectation": "any"
  },
  "options": { "confirmBulk": true }
}
```

## 8.3 Output (Flow return payload)

### Purpose
Deterministic, parseable summary for every run. Good for logging, dashboards, or chaining.

### JSON Schema (Draft-07)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Copy-Item Run Result",
  "type": "object",
  "additionalProperties": false,
  "required": ["operation","bulk","matchedCount","createdIds","updatedIds","warnings","errors"],
  "properties": {
    "operation": { "type": "string", "enum": ["create","update","upsert"] },
    "bulk": { "type": "boolean" },
    "quickMatch": { "type": "boolean" },
    "destMatch": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "column": { "type": "string" },
        "value": { }
      }
    },
    "matchMode": { "type": "string", "enum": ["simple","odata","caml","none"] },
    "matchCriteriaSummary": { "type": "string" },
    "matchedCount": { "type": "integer", "minimum": 0 },
    "createdIds": {
      "type": "array",
      "items": { "type": "integer", "minimum": 1 }
    },
    "updatedIds": {
      "type": "array",
      "items": { "type": "integer", "minimum": 1 }
    },
    "attachments": {
      "type": "object",
      "additionalProperties": false,
      "properties": {
        "mode": { "type": "string", "enum": ["none","append","overwrite","replace"] },
        "added": { "type": "integer", "minimum": 0 },
        "overwritten": { "type": "integer", "minimum": 0 },
        "replaced": { "type": "integer", "minimum": 0 },
        "skipped": { "type": "integer", "minimum": 0 }
      }
    },
    "fieldWarnings": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "properties": {
          "field": { "type": "string" },
          "message": { "type": "string" }
        }
      }
    },
    "warnings": {
      "type": "array",
      "items": { "type": "string" }
    },
    "errors": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

**Examples**  
**A) Quick upsert (single update, no attachments)**
```json
{
  "operation": "upsert",
  "bulk": false,
  "quickMatch": true,
  "destMatch": { "column": "Title", "value": "Task-001" },
  "matchMode": "simple",
  "matchCriteriaSummary": "Title eq 'Task-001'",
  "matchedCount": 1,
  "createdIds": [],
  "updatedIds": [123],
  "attachments": { "mode": "none", "added": 0, "overwritten": 0, "replaced": 0, "skipped": 0 },
  "fieldWarnings": [],
  "warnings": [],
  "errors": []
}
```

**B) Bulk update via OData (multi-value fields touched)**
```json
{
  "operation": "update",
  "bulk": true,
  "quickMatch": false,
  "matchMode": "odata",
  "matchCriteriaSummary": "Status eq 'Active' and Category eq 'Hardware'",
  "matchedCount": 37,
  "createdIds": [],
  "updatedIds": [101,102,103],
  "attachments": { "mode": "append", "added": 24, "overwritten": 0, "replaced": 0, "skipped": 5 },
  "fieldWarnings": [
    { "field": "Vendor", "message": "lookupByText ambiguous for 'Vendor A' — used first match" },
    { "field": "Stakeholders", "message": "1 user not found; remaining applied" }
  ],
  "warnings": ["MatchedCount > 30 — ensure bulk intended"],
  "errors": []
}
```

## 8.4 Contract Rules (defaults, precedence, coercion)

### Defaults
- If settings omitted → internal default:
```json
{ "version":"1.0", "match": { "mode":"simple", "criteria": { "$filter":"ID eq -1", "$top":1 }, "bulk": false, "expectation": "any" } }
```
- attachmentMode default: none  
- mapOnly default: true  
- operation default: upsert

### Precedence
1. If operation in {update, upsert} and both destMatchColumn & destMatchValue provided → build internal simple match.  
2. If settings.match is provided → settings wins (overrides quick match).  
3. operation=update with no match → fail with error; no writes.  
4. operation=upsert with no match → create.

### Coercion & formatting (writes)
- Use ValidateUpdateListItem. Send strings:  
  - Person/Lookup (single): "15" (ID as string).  
  - Person/Lookup (multi): ";#15;#27;#"  
  - Choice (multi): ";#High;#Low;#"  
  - DateTime: "YYYY-MM-DDTHH:MM:SSZ" (apply toUTC when needed).  
  - URL: "https://contoso.com, Label"  
- Unknown destination fields → skip + warn.  
- Hidden/readonly fields → skip + warn.

## 8.5 Backward/Forward Compatibility
- map: adding new optional attributes is allowed; existing keys unchanged.  
- settings: you may add new optional sections later; keep version and match shape intact.  
- Output: you may add new optional fields; existing required keys stay the same.
