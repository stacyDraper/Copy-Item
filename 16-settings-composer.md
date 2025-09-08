# 16. Settings Composer (Single‑Write Pattern)

## Purpose
Provide a single, authoritative method for assembling the `Settings` node during **Stage 1**.  
This pattern replaces piecemeal mutations with a **compose‑once, set‑once** approach that is easy to read, idempotent, and safe to re‑run.

---

## Principles
- **Single Write**: Build the entire `Settings` object in one Compose, then write it once to `v-Context.Settings`.
- **Fallback Order**: Prefer **Trigger** value → then **existing** `v-Context.Settings` value → then **final default**.
- **Special Case – Map**: Patch `Settings.Map` separately (avoid JSON quoting/escape issues when inlining).
- **Idempotent**: Re‑running Stage 1 won’t clobber existing state unless non‑blank trigger values are supplied.
- **Readable**: One JSON block = one place to reason about defaults and precedence.

---

## Steps

### 1) Compose — **C-Settings-Text**

> Build the whole Settings block in one place, preferring trigger values; otherwise fall back to existing settings; otherwise final default.

```json
{
  "Source": {
    "SiteUrl": "@{if(or(equals(outputs('C-InputFromTrigger')?['source']?['siteURL'], ''), equals(outputs('C-InputFromTrigger')?['source']?['siteURL'], null)), variables('v-Context')?['Settings']?['Source']?['SiteUrl'], outputs('C-InputFromTrigger')?['source']?['siteURL'])}",
    "ListName": "@{if(or(equals(outputs('C-InputFromTrigger')?['source']?['listName'], ''), equals(outputs('C-InputFromTrigger')?['source']?['listName'], null)), variables('v-Context')?['Settings']?['Source']?['ListName'], outputs('C-InputFromTrigger')?['source']?['listName'])}",
    "ItemId": @{if(or(equals(outputs('C-InputFromTrigger')?['source']?['itemID'], ''), equals(outputs('C-InputFromTrigger')?['source']?['itemID'], null)),
                 int(coalesce(variables('v-Context')?['Settings']?['Source']?['ItemId'], 0)),
                 int(outputs('C-InputFromTrigger')?['source']?['itemID']))}
  },

  "Dest": {
    "SiteUrl": "@{if(or(equals(outputs('C-InputFromTrigger')?['dest']?['siteURL'], ''), equals(outputs('C-InputFromTrigger')?['dest']?['siteURL'], null)), variables('v-Context')?['Settings']?['Dest']?['SiteUrl'], outputs('C-InputFromTrigger')?['dest']?['siteURL'])}",
    "ListName": "@{if(or(equals(outputs('C-InputFromTrigger')?['dest']?['listName'], ''), equals(outputs('C-InputFromTrigger')?['dest']?['listName'], null)), variables('v-Context')?['Settings']?['Dest']?['ListName'], outputs('C-InputFromTrigger')?['dest']?['listName'])}"
  },

  "QuickMatch": {
    "Column": "@{if(or(equals(outputs('C-InputFromTrigger')?['quickMatch']?['field'], ''), equals(outputs('C-InputFromTrigger')?['quickMatch']?['field'], null)), variables('v-Context')?['Settings']?['QuickMatch']?['Column'], outputs('C-InputFromTrigger')?['quickMatch']?['field'])}",
    "Value": "@{if(or(equals(outputs('C-InputFromTrigger')?['quickMatch']?['value'], ''), equals(outputs('C-InputFromTrigger')?['quickMatch']?['value'], null)), variables('v-Context')?['Settings']?['QuickMatch']?['Value'], outputs('C-InputFromTrigger')?['quickMatch']?['value'])}"
  },

  "Filter": {
    "Type": "@{if(or(equals(outputs('C-InputFromTrigger')?['filter']?['type'], ''), equals(outputs('C-InputFromTrigger')?['filter']?['type'], null)), variables('v-Context')?['Settings']?['Filter']?['Type'], outputs('C-InputFromTrigger')?['filter']?['type'])}",
    "Text": "@{if(or(equals(outputs('C-InputFromTrigger')?['filter']?['text'], ''), equals(outputs('C-InputFromTrigger')?['filter']?['text'], null)), variables('v-Context')?['Settings']?['Filter']?['Text'], outputs('C-InputFromTrigger')?['filter']?['text'])}"
  },

  "OperationMode": "@{if(or(equals(outputs('C-InputFromTrigger')?['operation'], ''), equals(outputs('C-InputFromTrigger')?['operation'], null)),
                            coalesce(variables('v-Context')?['Settings']?['OperationMode'], 'upsert'),
                            toLower(outputs('C-InputFromTrigger')?['operation']))}",

  "AttachmentMode": "@{if(or(equals(outputs('C-InputFromTrigger')?['attachmentModeRaw'], ''), equals(outputs('C-InputFromTrigger')?['attachmentModeRaw'], null)),
                              coalesce(variables('v-Context')?['Settings']?['AttachmentMode'], 'none'),
                              toLower(outputs('C-InputFromTrigger')?['attachmentModeRaw']))}",

  "MapOnly": @{if(or(equals(outputs('C-InputFromTrigger')?['mapOnly'], ''), equals(outputs('C-InputFromTrigger')?['mapOnly'], null)),
                 coalesce(variables('v-Context')?['Settings']?['MapOnly'], true),
                 bool(outputs('C-InputFromTrigger')?['mapOnly']))},

  "Bulk": @{if(or(equals(outputs('C-InputFromTrigger')?['bulk'], ''), equals(outputs('C-InputFromTrigger')?['bulk'], null)),
             coalesce(variables('v-Context')?['Settings']?['Bulk'], false),
             bool(outputs('C-InputFromTrigger')?['bulk']))},

  "Map": @{if(equals(variables('v-Context')?['Settings']?['Map'], null), json('{}'), variables('v-Context')?['Settings']?['Map'])},

  "Version": "@{coalesce(variables('v-Context')?['Settings']?['Version'], variables('v-Context')?['Version'], '1.0')}"
}
```

### 2) Set variable — write the whole block once
```text
@setProperty(variables('v-Context'), 'Settings', json(outputs('C-Settings-Text')))
```

### 3) Optional — apply a new Map only if provided (else keep old)
> Preserve existing `Settings.Map` unless a non‑blank trigger `map` string is provided.

```text
@setProperty(
  variables('v-Context'),
  'Settings',
  setProperty(
    variables('v-Context')?['Settings'],
    'Map',
    if(
      or(equals(outputs('C-InputFromTrigger')?['map'], ''), equals(outputs('C-InputFromTrigger')?['map'], null)),
      variables('v-Context')?['Settings']?['Map'],
      json(outputs('C-InputFromTrigger')?['map'])
    )
  )
)
```

---

## Validation Notes
- Use a single guard condition to verify required pieces before Stage 2:
  - `Source.SiteUrl`, `Source.ListName`, `Dest.SiteUrl`, `Dest.ListName`
  - `OperationMode` in `create|update|upsert`
  - `AttachmentMode` in `none|append|overwrite|replace`

---

## Cross‑References
- **08-json-contracts.md** – Contract philosophy behind settings shape.  
- **13-action-skeleton.md** – Where the Compose/Set lives in Stage 1.  
- **14-naming-conventions.md** – Naming consistency (`C-Settings-Text`, `v-Context`).  
- **15-build-checklist.md** – Checklist item enforcing single‑write updates.  

---

## Changelog
- **v1.0** — Initial publication of Settings Composer (compose‑once, set‑once).
