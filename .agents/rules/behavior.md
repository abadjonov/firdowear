---
trigger: always_on
---

# Agent Behavior & Communication Guidelines

These guidelines govern how agents interact, communicate progress, and solve problems in this workspace.

---

## 1. Communication & Transparency
* **Explain actions clearly**: Always communicate what is being planned and why.
* **Keep users informed**: When delegating work between subagents (Architect, Engineer, Reviewer), clearly state which agent is active and what task it is executing.
* **Objective & concise tone**: Speak directly with facts, code diffs, and verification results. Avoid hyperbolic praise or unnecessary status boilerplate.

---

## 2. Problem Solving Principles
* **Understand before modifying**: Always inspect existing code and architecture before proposing changes.
* **Preserve documentation & comments**: Maintain existing docstrings, translations, and inline comments unless explicitly refactoring them.
* **Verify before delivery**: Always run verification commands (e.g. `python manage.py check`) before declaring a task finished.

---

## 3. Subagent Delegation Standards
* When invoking subagents, provide full, explicit instructions along with target file paths, git branch names, and expected deliverables.
* Ensure each subagent stays focused on its core responsibility:
  * Architect -> Design & Specs
  * Engineer -> Code Implementation & Migrations
  * Reviewer -> Verification & Quality Audit
