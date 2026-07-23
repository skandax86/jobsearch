# Resume Domain

**Document ID:** 03.01  
**Version:** 1.0  
**Status:** Draft  
**Last Updated:** 2026-07-12

---

## 1. Purpose

Define how CareerPilot AI ingests a source resume, establishes a canonical structured representation, produces truthful job-tailored content, and renders validated PDF, DOCX, or HTML documents.

The Resume domain separates **content generation** from **document rendering**. A PDF is a rendered artifact; it is never the editable source of truth.

## 2. Core Pipeline

```text
Source PDF / DOCX / HTML
        │
        ▼
Parser and extraction review
        │
        ▼
Canonical Resume JSON
        │
        ▼
Job analysis + Resume Optimizer
        │
        ▼
Tailored Resume Content JSON
        │
        ▼
Approved template + deterministic renderer
   ┌────┼─────────┐
   ▼    ▼         ▼
LaTeX  DOCX      HTML
   │    │         │
   ▼    ▼         ▼
PDF   DOCX      PDF / HTML
```

The LLM may create a structured content proposal only. It must not generate raw LaTeX, DOCX XML, or free-form HTML/CSS as the primary document-production path.

## 3. Goals

- Preserve candidate facts and source provenance.
- Support tailored, ATS-oriented content without fabrication.
- Render the same approved content to multiple formats.
- Produce deterministic, reproducible artifacts from versioned templates.
- Support user editing and portals that require DOCX.

## 4. Aggregate and Entities

| Entity | Responsibility |
|---|---|
| `Resume` | aggregate root; owns lifecycle, access, active version, and archival |
| `ResumeVersion` | immutable source, verified, or tailored content snapshot |
| `ResumeContent` | typed canonical JSON; no renderer-specific markup |
| `ResumeTemplate` | reviewed, versioned layout rules and assets |
| `ResumeRender` | immutable output with checksum, format, renderer/template versions, and validation report |

## 5. Canonical Content Contract

The canonical JSON schema is versioned and validated. It carries contact details, headline, summary, experience, education, skills, projects, certifications, languages, links, ordering, and source provenance. Generated facts must retain a `source_fact_id` or equivalent approved reference.

```json
{
  "schema_version": "1.0",
  "headline": "Data Engineer",
  "experience": [{
    "id": "experience_01",
    "company": "Example Company",
    "title": "Data Engineer",
    "bullets": ["Verified achievement."],
    "source_fact_ids": ["fact_123"]
  }],
  "skills": [],
  "education": []
}
```

## 6. Tailoring Rules

The optimizer may select, reorder, summarize, or rewrite verified material; improve keyword coverage using verified information; and recommend missing skills as recommendations.

It must never invent or inflate experience, dates, titles, employers, metrics, skills, credentials, visa status, work authorization, or language fluency. Any factual change requires explicit user approval.

## 7. Renderer Contract

Renderers accept `ResumeContent`, `TemplateDefinition`, and `RenderOptions`; they return an artifact plus a structured validation report.

| Renderer | Output | Intended use |
|---|---|---|
| LaTeX | text-selectable PDF | primary professional PDF output |
| DOCX | editable DOCX | portals and candidate editing |
| HTML | HTML or print-ready PDF | preview and web delivery |

LaTeX is the preferred PDF renderer because template-driven compilation provides consistent professional typography. It is not the sole renderer.

## 8. Versioning and Provenance

An application references immutable snapshots of the content version, render artifact/checksum, template version, renderer version, and job-description snapshot. Rendering is idempotent for the content checksum, template version, renderer version, and options.

## 9. Safety and Quality Controls

- Compile LaTeX in a network-isolated, resource-limited sandbox with shell escape disabled.
- Store templates in Git and treat them as reviewed code.
- Validate output MIME type, checksum, page count, required sections, and text extractability.
- Run ATS checks against rendered text as well as canonical content.
- Never log resume content, raw prompts, or source documents.

## 10. States and Events

```text
Source: uploaded → parsing → extracted → needs_review / verified → archived
Tailoring: proposed → awaiting_approval → approved → superseded
Render: queued → rendering → validated → available / failed
```

Events: `ResumeUploaded`, `ResumeParsed`, `ResumeContentVerified`, `ResumeTailoringProposed`, `ResumeTailoringApproved`, `ResumeRenderRequested`, `ResumeRendered`, and `ResumeRenderFailed`.

## 11. Responsibilities

| Component | Responsibility |
|---|---|
| Parser | source file → extraction proposal; never directly verifies facts |
| Resume Service | validation, persistence, versioning, authorization, and events |
| Resume Optimizer Agent | canonical content + job snapshot → structured tailoring proposal |
| Template Selector | approved template selection based on user choice and target requirements |
| Renderer Worker | deterministic render and validation; never modifies content or calls an LLM |
| Application Service | selects approved artifact and records submission evidence |

## 12. Related Documents

- [00-Domain-Overview.md](00-Domain-Overview.md)
- [05-AI-Agent-Layer.md](../02-architecture/05-AI-Agent-Layer.md)
- [09-Data-Layer.md](../02-architecture/09-Data-Layer.md)
- [10-Storage-Layer.md](../02-architecture/10-Storage-Layer.md)
- [11-Worker-Architecture.md](../02-architecture/11-Worker-Architecture.md)
- [13-Security-Architecture.md](../02-architecture/13-Security-Architecture.md)
