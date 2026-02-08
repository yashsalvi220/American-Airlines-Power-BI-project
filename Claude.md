# WAT Framework

**Workflows, Agents, Tools** — an architecture that separates probabilistic AI reasoning from deterministic code execution to produce reliable outcomes.

## Architecture

### Layer 1: Workflows (The Instructions)

Markdown SOPs stored in `workflows/`. Each workflow defines:

- **Objective** — what needs to be accomplished
- **Required inputs** — data, credentials, or context needed before starting
- **Tool sequence** — which scripts to run and in what order
- **Expected outputs** — what a successful run looks like
- **Edge cases** — how to handle failures and exceptions

Workflows are written in plain language. They evolve as the system learns.

### Layer 2: Agents (The Decision-Maker)

The AI layer responsible for intelligent coordination:

- Read the relevant workflow
- Run tools in the correct sequence
- Handle failures gracefully
- Ask clarifying questions when inputs are ambiguous

Agents connect intent to execution. They don't perform deterministic work directly — they delegate to tools.

### Layer 3: Tools (The Execution)

Python scripts in `tools/` that do the actual work:

- API calls, data transformations, file operations, database queries
- Credentials and API keys are stored in `.env`
- Each script is consistent, testable, and fast

**Why this separation matters:** When AI handles every step directly, accuracy compounds downward. Five steps at 90% accuracy each yields ~59% overall success. Offloading execution to deterministic scripts keeps accuracy high while the agent focuses on orchestration.

## Directory Layout

```
.tmp/           # Temporary files (scraped data, intermediate exports). Regenerated as needed.
tools/          # Python scripts for deterministic execution
workflows/      # Markdown SOPs defining what to do and how
.env            # API keys and environment variables (secrets stay here only)
```

- **Deliverables** go to cloud services (Google Sheets, Slides, etc.) where stakeholders can access them directly.
- **Intermediates** in `.tmp/` are disposable and can be regenerated at any time.

## Operating Principles

### 1. Reuse before building

Check `tools/` for existing scripts before creating new ones. Only write new tools when nothing covers the task.

### 2. Fail forward

When something breaks:

1. Read the full error message and trace
2. Fix the script and retest
3. Document the lesson in the workflow
4. Move on with a stronger system

### 3. Keep workflows current

Update workflows when you discover better methods, new constraints, or recurring issues. Workflows are living documents — they improve with use.

## The Self-Improvement Loop

Every failure strengthens the system:

1. **Identify** what broke
2. **Fix** the tool
3. **Verify** the fix works
4. **Update** the workflow with the new approach
5. **Continue** with a more robust system

This loop is how the framework gets better over time without manual intervention.

## Active Workflows

| Workflow | Description | Entry Point |
|----------|-------------|-------------|
| [LinkedIn Lead Scraper](workflows/linkedin_lead_scraper.md) | Find LinkedIn contacts by profession & location, export to Google Sheets | `python tools/lead_pipeline.py --profession "…" --location "…"` |
