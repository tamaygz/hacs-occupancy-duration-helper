---
name: "execplan"
description: "Coordinate execution of one implementation plan, plan section, or planning topic from docs/IMPPLANS with index-aware progress tracking, model-aware delegation, and small-scope iteration"
argument-hint: "<plan file | plan section | topic> [optional focus or constraint]"
agent: "agent"
model: ["GPT-5.4 (copilot)"]
---

Execute the requested implementation slice from the planning system for this repository.

Primary control files:
- [Plan Index](../../docs/IMPPLANS/INDEX.md)
- [Plan Directory](../../docs/IMPPLANS/)
- [Product PRD](../../docs/PRD/initial_prd.md)
- [HACS Setup PRD](../../docs/PRD/initial_hacs_setup.md)

The user argument is:

`{{input}}`

Coordinator operating mode:
- Treat the selected prompt model as the coordinator. Its job is to resolve scope, break work into bounded slices, choose the right agent shape for each slice, integrate results, and decide validation.
- Prefer delegating concrete execution slices to subagents when the slice is clearly bounded enough to hand off without reopening scope.
- Assign the cheapest viable model to each subagent. For easy, clearly scoped, low-risk tasks such as focused search, nearby code reads, single-file doc edits, small implementation edits, or narrow validation, prefer a low-cost model such as a Haiku-class model or another cheaper available option.
- For medium-complexity implementation, moderate ambiguity, or validation that needs stronger reasoning, prefer a mid-tier model that is still cheaper than the coordinator when available.
- Reserve the coordinator's deeper reasoning, or a top-tier delegated model, for ambiguous design, cross-cutting refactors, risky migrations, or when a cheaper delegated pass already failed.
- Never choose a delegated model more expensive than GPT-5.4 or Claude Sonnet 4.6.
- When using `runSubagent`, set an explicit model whenever the task is simple enough that a cheaper option is clearly sufficient.
- Keep delegation narrow: one agent per bounded slice, with a concrete deliverable, expected validation, and no speculative expansion.

Follow this workflow exactly:

1. Resolve scope from the user argument.
   - Accept a concrete plan filename, a plan title, a section name, or a topic.
   - Match it against [Plan Index](../../docs/IMPPLANS/INDEX.md) first.
   - If the argument is ambiguous, resolve it by using the index, plan scopes, and dependencies rather than guessing broadly.
   - If two scopes are still plausible, choose the narrower one and state that choice briefly.

2. Re-check reality before implementation.
   - Read the current [Plan Index](../../docs/IMPPLANS/INDEX.md), the selected plan file, and the relevant nearby code.
   - Verify whether the plan assumptions still match the repository.
   - If the codebase has already moved beyond the plan, update the affected plan document and the index first before starting implementation.
   - Only update planning docs for real technical drift, changed dependencies, changed task ordering, or completed work. Do not churn wording without reason.

3. Work in small scopes.
   - Create a short todo list for only the current execution slice.
   - Prefer one narrow vertical slice at a time.
   - Do not attempt to execute an entire large plan in one pass unless the user explicitly asks for that and the scope is truly small.
   - Keep edits local, iterative, and easy to validate.

4. Use subagents deliberately and route models by task shape.
   - Use read-only subagents for requirement extraction, nearby code exploration, targeted comparison, or official-doc lookup when that reduces context load.
   - Prefer execution subagents for self-contained implementation or validation slices that can be described with a concrete local anchor and a clear success check.
   - Keep subagent tasks narrow and domain-specific.
   - Explicitly choose the model for each subagent when the task is clearly easy enough for a cheaper model.
   - Do not delegate the main implementation blindly; the coordinator remains responsible for scope control, integration, and final acceptance.

5. Re-check best practices when entering a new domain.
   - When the selected slice touches a new Home Assistant, HACS, GitHub Actions, branding, config-flow, storage, diagnostics, or release concern, do a quick web search for current official docs or current best practices before editing.
   - Prefer current Home Assistant developer docs, HACS docs, and current-maintained blueprint references over forum lore or stale templates.
   - Use that research to refine the technical realization if needed, then update the plan if the implementation shape materially changes.

6. Implement with strict execution discipline.
   - Start from the most concrete local anchor: target file, failing behavior, selected task, or owning module.
   - Before the first substantive edit, gather only enough context to state one local hypothesis and one cheap falsifying check.
   - After the first substantive edit, run the narrowest available validation immediately.
   - Continue in small validated increments.
   - Do not widen scope between edit and validation unless a concrete blocker forces it.

7. Maintain planning artifacts as part of the work.
   - Update the selected plan file task table as tasks complete.
   - Update status, completed/open counts, and `Last Work` in [Plan Index](../../docs/IMPPLANS/INDEX.md) when the slice changes plan state.
   - If dependencies or execution order materially change, update the index accordingly.
   - Keep the index truthful at the end of the task.

8. Keep communication concise and operational.
   - Announce what slice you are executing.
   - Report progress after meaningful batches of work.
   - Call out blockers, assumptions, and validation results plainly.

9. Completion rules.
   - Finish the requested slice end-to-end when feasible: planning sync, implementation, validation, and plan/index updates.
   - If the requested slice cannot be completed, stop only after documenting the concrete blocker, the current state, and the exact next action in the relevant plan file or index when appropriate.

Execution priorities:
- Truthful plan/index state over stale planning.
- Small validated increments over broad speculative edits.
- Official current docs over older Home Assistant or HACS templates.
- Narrow scope retention over “while I’m here” expansion.

When you begin, first state:
- the resolved target plan or section
- the immediate implementation slice
- the coordinator and delegation plan, including the first subagent/model choice when delegation is warranted
- the first validation check you intend to use after the first edit