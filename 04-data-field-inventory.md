# Copy-Item Flow — Data & Field Inventory (MVP Baseline)

## 4.1 Representative Lists / Libraries

We’ll define at least 3 representative lists for testing and validation.  
These should live in a test site collection and remain stable during MVP development.

| List Name | Purpose | Notes |
|-----------|---------|-------|
| Tasks     | Standard single-value fields, common transforms | Text, Number, DateTime, Person, Choice |
| Projects  | Rich multi-value fields, lookups | Multi-choice, Multi-person, Multi-lookup, DateTime |
| Inventory | URL fields, attachment-heavy | Includes attachments in every item; also has Lookup to a Vendors list |

---

## 4.2 Supporting Lookup Lists

For Lookup tests, we need small supporting lists to resolve IDs and text values.

| List Name  | Purpose                         | Example Fields                        |
|------------|---------------------------------|----------------------------------------|
| Departments| Lookup target for Tasks.Department | Title (text)                           |
| Vendors    | Lookup target for Inventory.Vendor | Title (text), VendorCode (text)        |

---

## 4.3 Field Catalog Template

We’ll maintain a table for each representative list with key field details.  
Fill this out once and keep it up to date to avoid mid-run surprises.

| Internal Name | Display Name  | Type     | Single/Multi | Required | Unique | Indexed | Notes / Special Handling |
|---------------|---------------|----------|--------------|----------|--------|---------|--------------------------|
| Title         | Task Name     | Text     | Single       | Yes      | No     | Yes     | Primary key in many tests |
| DueDate       | Due Date      | DateTime | Single       | No       | No     | No      | Must be converted to UTC |
| Owner         | Owner         | Person   | Single       | No       | No     | No      | Use `ensureUser` |
| Department    | Department    | Lookup   | Single       | No       | No     | No      | Target: Departments list |
| Tags          | Tags          | Choice   | Multi        | No       | No     | No      | Values: [“High”, “Medium”, “Low”] |
| Stakeholders  | Stakeholders  | Person   | Multi        | No       | No     | No      | Use array + `ensureUser` |
| Vendor        | Vendor        | Lookup   | Multi        | No       | No     | No      | Target: Vendors list |
| ProductURL    | Product URL   | URL      | Single       | No       | No     | No      | Format: {Url, Description} |

---

## 4.4 Test Dataset Guidelines

- At least 5 items per list with varied data:  
  - Some items missing optional fields (tests defaults).  
  - Some with multiple People/Lookup/Choice values.  
  - Some with attachments (1–5 files).  
  - Some with special characters in text (e.g., quotes, commas, HTML tags).  
- For Lookup/Choice:  
  - Include values that exist in the target.  
  - Include at least one non-existent value (tests error/warning path).  
- For Person:  
  - Include valid and invalid user emails (tests `ensureUser` resolution + failure).  

---

## 4.5 Why This Inventory Matters

- Guarantees all MVP field types are tested before release.  
- Makes it clear which fields require transforms.  
- Allows us to replay the same runs for regression testing after changes.  
- Prevents “surprise” schema mismatches at deployment.
