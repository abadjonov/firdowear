# AI Collaboration & Multi-Agent Guide (Firdowear)

This document provides essential context and rules for AI models operating within the **Firdowear** repository. Adhering to these guidelines ensures architectural integrity, security, and consistent code quality across all features.

---

## 1. Project Overview & Business Domain

* **Primary Purpose**: Firdowear is an online showcase and ordering web service for a boys' clothing and footwear store (ages 0–18).
* **Languages & Translations**: Uzbek (`uz`) and Russian (`ru`) using `django-modeltranslation` for database content and standard Django gettext for templates/UI.
* **Core Apps**:
  * `products/`: Brands, Categories, Age Groups, Size Types, Sizes, Colors, Products, Images, and Variants (inventory stock).
  * `orders/`: Customer order processing, checkout, order items, and operator notifications via Telegram Bot.
  * `pages/`: Static and informational views (Homepage, Store location, Contact).
  * `config/`: Project settings, URL routing, WSGI/ASGI configurations.
  * `templates/`: HTML templates (`base.html`, app templates, includes).

---

## 2. Core Technologies & Stack

* **Language**: Python 3.10+
* **Web Framework**: Django 5.1.x
* **Admin Interface**: `django-unfold`
* **Translation**: `django-modeltranslation` (`name_uz`, `name_ru`), `polib`
* **Databases**:
  * Development: SQLite (`db.sqlite3`)
  * Production: PostgreSQL (`psycopg[binary]`, `dj-database-url`)
* **Integrations**: Telegram Bot API for real-time order alerts to operator chat
* **Media & Static**: Pillow for image processing, WhiteNoise for static files
* **Process / Container**: Gunicorn, Docker Compose, uv / pip

---

## 3. Git Branching Strategy (MANDATORY)

To preserve code stability, this project enforces a strict **Git Flow** policy:

```
[develop] ──────────────────────────────────────────► (Merge on SUCCESS) ──► [develop]
    │                                                      ▲
    └────► git checkout -b feat/<name> ──► [feat/<name>] ──┘
           (Engineer commits & tests)     (Reviewer checks)
```

1. **Protected Branches**: `main` (production-ready) and `develop` (active integration).
   * **STRICT RULE**: **NEVER write code or make direct commits to `main` or `develop`.**
2. **Feature Branches**:
   * Every task, bug fix, or feature MUST be executed on a dedicated branch created from `develop`:
     ```bash
     git checkout develop && git pull
     git checkout -b feat/<feature-name>
     ```
3. **Review & Integration**:
   * The `engineer` works exclusively on `feat/<feature-name>`.
   * The `reviewer` audits the changes using `git diff develop...feat/<feature-name>`.
   * **If `[STATUS: SUCCESS]`**: The Orchestrator merges `feat/<feature-name>` into `develop` using `git merge --no-ff feat/<feature-name>` and deletes the feature branch (`git branch -d feat/<feature-name>`).
   * **If `[STATUS: FAILED]`**: The feature branch is preserved, and the `engineer` makes corrective commits on it until approval is granted.

---

## 4. Multi-Agent Team Architecture

The multi-agent workflow consists of four specialized roles:

1. **Master Orchestrator (Root Agent)**:
   * Front-facing agent interacting with the user.
   * Manages Git branch lifecycle (`checkout`, `merge`, `branch -d`).
   * Sequentially delegates work: Orchestrator → Architect → Engineer → Reviewer.
2. **Technical Architect (`.agents/agents/architect/agent.md`)**:
   * Analyzes requirements, checks codebase context, designs Django models/views/integrations.
   * Produces a comprehensive specification in `plans/<feature-name>-design.md`.
3. **Software Engineer (`.agents/agents/engineer/agent.md`)**:
   * Operates strictly on `feat/<feature-name>`.
   * Writes Python/Django code, migrations, templates, and self-checks.
4. **Code Reviewer (`.agents/agents/reviewer/agent.md`)**:
   * Analyzes diff against `develop`.
   * Checks for N+1 queries, Django security, translation completeness, and code style.
   * Returns explicit `[STATUS: SUCCESS]` or `[STATUS: FAILED]`.

---

## 5. Coding Conventions & Best Practices

* **PEP 8**: `snake_case` for functions/variables/files, `PascalCase` for classes, `UPPER_CASE` for constants.
* **ORM Performance**: Always use `select_related()` for ForeignKey/OneToOne and `prefetch_related()` for ManyToMany/Reverse relations. Prevent N+1 queries in views and template rendering.
* **Translations**:
  * In code: use `from django.utils.translation import gettext_lazy as _`.
  * In templates: use `{% load i18n %}` and `{% trans "..." %}` or `{% blocktrans %}`.
  * Register translatable model fields in `translation.py`.
* **Zero Guesswork**: When unsure about requirements or credentials, check `.env.example` and [PLAN.md](PLAN.md) before implementing.
