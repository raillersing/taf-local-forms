# Prompt Contracts — TAf Local Forms

These are reusable prompt templates for agents. Keep them short.
Reference AGENTS.md and relevant skills instead of duplicating rules.

## Audit task

Read-only. Inspect a component and report findings.

```
Inspect {component} for {concern}.

Requirements:
- Read-only: do not modify any file.
- Report findings with severity (low / medium / high / critical).
- Include file/line references for each finding.
- If clean, state "No findings."
```

## Implementation task

Implement a slice of work.

```
Implement {slice}.

Context:
- Branch: {branch}
- Current commit: {sha}

Rules:
- Follow AGENTS.md workflow.
- Stay within allowed scope.
- Do not change models, migrations, scoring, or anti-duplicate logic unless explicitly requested.
- Run quality gates before commit.
- Commit only when all gates pass.
```

## Review task

Read-only review of completed work.

```
Review {change} against {checklist}.

Requirements:
- Read-only: do not modify any file.
- Inspect: diff, tests, validation evidence.
- Verdict: APPROVE / REQUEST_CHANGES / BLOCK.
- If REQUEST_CHANGES or BLOCK, list specific findings with severity.
```

## Release task

Prepare and execute a release.

```
Run release checklist for version {version}.

Steps:
1. Read docs/ai-agents/release-checklist.md.
2. Execute each step in order.
3. If any step fails, stop and report.
4. If all steps pass, prepare release notes and tag.
```

## Emergency / debug task

Reproduce and isolate a runtime issue.

```
Reproduce {issue}.

Steps:
1. Check current state (status, log, Docker).
2. Try to reproduce with curl or browser.
3. Isolate root cause (code, config, network, Docker).
4. Propose fix without committing.
5. Stop for human approval before modifying any file.
```
