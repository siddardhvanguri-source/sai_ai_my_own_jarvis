---
name: find-ui-templates
description: Search the web and curate good UI/website templates or design references for a stated use case (e.g. "SaaS landing page", "dashboard", "portfolio"), or for whatever the user is currently building if no use case is given. Trigger on requests like "find me a template for X", "good UI for Y", "search motion.dev / awwwards / mobbin for Z", or "what should this page look like".
---

# Find UI templates

You are picking design references for a real build, not writing a listicle. The
person wants 3-5 things worth opening, each with a reason, not twenty links.

## Step 1 — Pin down the use case

If the user gave a use case, use it as-is. If they said "find me something good"
with no context, check what they're currently building (recent conversation,
open project) before asking. Only ask a direct question if genuinely nothing
points to an answer. Note explicitly whether they want:

- **Full page / site templates** (landing page, dashboard, portfolio, docs site)
- **Component or interaction patterns** (a pricing table, a nav, a modal, an
  animation) — this is what motion.dev's examples and MCP are for
- **Pure inspiration / art direction** (mood, color, layout ideas — not code)

These pull from different sources, so don't default to one search engine for
everything.

## Step 2 — Search the right sources for the request

**Full-page templates & component libraries (copy-ready code):**
- Kokonut UI (kokonutui.com) — 100+ animated, modern UI components with Next.js/React, Tailwind CSS v4, Motion, and shadcn registry integration (`@kokonutui/<name>`)
- 21st.dev — modern React/Tailwind component marketplace, searchable by type
- Aceternity UI, Magic UI — animated component libraries (Tailwind + Framer/Motion)
- HyperUI, Tailwind UI, shadcn/ui blocks — clean, production-grade component sets
- Framer Marketplace — full site templates, drag-and-drop, good for non-devs
- UI8, Creative Tim — paid but high-quality full template packs

**Motion / micro-interactions:**
- motion.dev/examples — filter by tutorial/grade; if the user has Motion+, use
  the Motion MCP server directly instead of scraping the page

**Design inspiration (not code, but sets direction):**
- Awwwards, Land-book, Lapa Ninja, SaaS Landing Page, Mobbin (mobile + web
  app UI patterns, great for flows not just single screens), Dribbble

Run searches specific to the use case and the site, not generic ones — e.g.
"site:21st.dev pricing section" beats "good ui templates". Open enough results
to actually compare, don't judge off a thumbnail.

## Step 3 — Judge quality, don't just collect links

For each candidate, weigh:
- Fits the stated use case and target audience (a fintech dashboard and a
  DTC landing page want different things)
- Buildable with the stack this project already uses (check CLAUDE.md /
  project context — don't recommend a heavy Framer template into a
  vanilla-JS or non-React codebase without saying so)
- Actually distinctive — skip anything that reads as generic Bootstrap-era
  SaaS boilerplate unless the user explicitly wants safe and standard
- License/cost — flag anything paid before recommending it as *the* pick

## Step 4 — Present a shortlist, not a dump

For each of the 3-5 picks give: name/source, one line on why it fits this
specific use case, and the link. Group by category if you pulled from more
than one (e.g. "Full page" vs "Components" vs "Inspiration only"). End with
your actual top pick and why, if one clearly stands out — don't make the user
do the deciding work you were asked to do.

If nothing found is genuinely good, say so plainly rather than padding the
list to hit five.
