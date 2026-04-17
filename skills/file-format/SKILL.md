---
name: file-format
description: "Use this skill BEFORE generating any file output — PDF, PPTX, DOCX, XLSX, HTML, or Markdown. Triggers include: any request to create, produce, or generate a document, presentation, spreadsheet, report, memo, proposal, invoice, resume, or any formatted file. Also use when the user asks to update formatting preferences, style standards, or brand guidelines. This skill provides a 3-layer formatting lookup: global standards, file-type rules, and document-purpose rules. Always invoke this skill before the file-type-specific skill (docx, pptx, xlsx, pdf)."
---

# File Format Standards

## Overview

This skill provides consistent formatting and design standards across all file outputs. It ensures consistent branding, typography, layout, and structure across every file type and document purpose the agent generates.

Standards live in `resources/FORMAT.md`, organized into three layers that the agent reads on demand.

---

## How to Read FORMAT.md

`resources/FORMAT.md` is divided into sections using `## section-name` headings. Each section is separated by a `---` horizontal rule divider.

**To extract the formatting rules you need:**

1. Use grep to search `resources/FORMAT.md` for the section keyword (e.g., `"## pptx"`, `"## finance-report"`)
2. Read from the matched `## heading` down to the next `---` divider — that is the complete section
3. Each section is self-contained: everything between `## heading` and the next `---` belongs to that section

**Section types in FORMAT.md:**

- `## global` — universal standards (always at the top)
- `## <file-type>` — file-format-specific rules (e.g., `## pptx`, `## docx`, `## xlsx`, `## pdf`, `## md`, `## html`)
- `## <purpose>` — document-purpose-specific rules (e.g., `## finance-report`, `## seo-audit`, `## meeting-minutes`)

Users can add their own file-type or purpose sections at any time. Do not assume the list is fixed — always search for a match.

---

## 3-Layer Lookup Process

**Before generating any file, perform these lookups IN ORDER:**

### Layer 1: Global Standards (ALWAYS read)

Search for `## global` in `resources/FORMAT.md`. Read the entire section.

This section defines universal rules: brand color palette, typography scale, writing conventions, and general layout. These apply to every file you generate.

### Layer 2: File-Type Standards (ALWAYS read)

Search `resources/FORMAT.md` for the `## <file-type>` section matching your output format. The section name matches the file extension or format name.

Examples:
- Generating a `.pptx` file → search for `## pptx`
- Generating a `.docx` file → search for `## docx`
- Generating a `.pdf` file → search for `## pdf`

If the exact file type is not found, fall back to Layer 1 global standards only.

These sections override or extend global standards with format-specific rules (slide setup, page margins, cell formatting, etc.). Each file-type section typically contains: setup, color application, typography overrides, structure rules, and common mistakes to avoid.

### Layer 3: Document Purpose Standards (read WHEN APPLICABLE)

Search `resources/FORMAT.md` for the `## <purpose>` section matching the document's purpose or category. Purpose sections are listed after the file-type sections under the heading `# Document Purpose Standards`.

Examples:
- Creating a quarterly earnings report → search for `## finance-report`
- Creating an SEO audit → search for `## seo-audit`
- Creating meeting notes → search for `## meeting-minutes`

**How to find the right purpose section:** Identify the purpose or category of the document from the user's request, then search for it as a keyword in `resources/FORMAT.md`. If no matching purpose section exists, skip Layer 3.

Purpose sections follow the same structure as file-type sections — they provide formatting overrides (color application, typography, layout, data formatting, structure rules, common mistakes), not content guidance. Apply them on top of Layers 1 and 2.

If no purpose section matches the user's request, skip Layer 3.

---

## Conflict Resolution

When rules from different layers conflict:

- **Layer 3 (purpose) overrides Layer 2 (file-type) overrides Layer 1 (global)**
- The more specific rule always wins
- Example: Global says "left-align body text", but `## legal-doc` says "justified text is acceptable" — use justified for legal documents

---

## Multi-Purpose Documents

Some requests span multiple purposes (e.g., "create a financial proposal"). When this happens:

1. Read all applicable purpose sections
2. Apply all non-conflicting rules from each
3. For conflicts between purpose sections, prefer the section closer to the user's primary intent
4. When in doubt, ask the user which purpose takes priority

---

## Purpose Detection

When the user's request does not explicitly name a purpose category, infer it from context:

- "quarterly earnings" or "P&L" or "budget" or "forecast" -> `## finance-report`
- "SEO" or "keyword ranking" or "backlink" or "site audit" -> `## seo-audit`
- "meeting notes" or "action items from the call" or "minutes" -> `## meeting-minutes`
- "pitch" or "proposal" or "RFP" -> `## proposal`
- "executive summary" or "brief" or "one-pager" -> `## executive-summary`
- "newsletter" or "internal update" or "company news" -> `## newsletter`
- "resume" or "CV" or "cover letter" -> `## resume`
- "contract" or "NDA" or "terms" or "agreement" -> `## legal-doc`

These are examples — not an exhaustive list. Users may add custom purpose sections. Always search FORMAT.md for a match based on the document's purpose keywords.

If the purpose is ambiguous, proceed with only Layers 1 and 2, or ask the user.

---

## Updating Standards

Users can request changes to formatting preferences. When they do:

1. Read the current `resources/FORMAT.md`
2. Identify the correct section to update (global, file-type, or purpose)
3. Make the edit within that section, following the existing structure pattern
4. Confirm the change with the user

To add a new file-type or purpose section:
1. Add it after the existing sections of the same type (file-type sections go before the `# Document Purpose Standards` heading, purpose sections go after)
2. Use `## section-name` as the heading
3. Follow the same subsection structure as existing sections (color application, typography, layout, structure rules, common mistakes to avoid)
4. End the section with a `---` divider
