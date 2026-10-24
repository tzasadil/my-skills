---
name: angular-developer
description: "Use when generating Angular code or giving architectural guidance: projects, components, services, HTTP, reactivity (signals, linkedSignal, resource, httpResource), forms, DI, routing, SSR, accessibility (ARIA), animations, styling (component styles, Tailwind), testing, naming, or CLI tooling."
license: MIT
metadata:
  author: Copyright 2026 Google LLC
  version: '1.0'
---

# Angular Developer Guidelines

Analyze the project's Angular version first. Practices and features vary by version. New CLI project: do not specify a version unless the user does.

Follow Angular's style guide. Scaffold with the CLI (components, services, directives, pipes, routes). After generating, `ng build`. Fix errors before proceeding. Do not skip.

## New projects

Latest stable unless the user specifies otherwise. Signal Forms for form management in new projects (stable in v22+): [signal-forms.md](references/signal-forms.md).

`ng new` execution:

1. User requested a version (e.g. Angular 15) -> `npx @angular/cli@<requested_version> new <project-name>`
2. Else `ng version` succeeds -> `ng new <project-name>`
3. Else `npx @angular/cli@latest new <project-name>`

## References (open only what the task needs)

**Components:** [components.md](references/components.md) · [inputs.md](references/inputs.md) · [outputs.md](references/outputs.md) · [host-elements.md](references/host-elements.md) · [naming-conventions.md](references/naming-conventions.md) (v20+ "Intent over Role"). Deeper: https://angular.dev/guide/components

**Reactivity:** [signals-overview.md](references/signals-overview.md) · [linked-signal.md](references/linked-signal.md) · [resource.md](references/resource.md) · [effects.md](references/effects.md). Persist a signal or adapt a getter/setter to `WritableSignal`: [templates.md](templates.md)

**HTTP:** [http-client.md](references/http-client.md)

**Forms.** New app on v22+ -> prefer Signal Forms. Older or existing forms -> match the app's current strategy. [signal-forms.md](references/signal-forms.md) · [template-driven-forms.md](references/template-driven-forms.md) · [reactive-forms.md](references/reactive-forms.md)

**DI:** [di-fundamentals.md](references/di-fundamentals.md) · [creating-services.md](references/creating-services.md) · [defining-providers.md](references/defining-providers.md) · [injection-context.md](references/injection-context.md) · [hierarchical-injectors.md](references/hierarchical-injectors.md)

**Pipes:** prefer in templates. Outside templates, do not inject pipe classes just to call `transform()`. [pipes.md](references/pipes.md)

**Aria** (Accordion, Listbox, Combobox, Menu, Tabs, Toolbar, Tree, Grid): [angular-aria.md](references/angular-aria.md)

**Routing:** [define-routes.md](references/define-routes.md) · [loading-strategies.md](references/loading-strategies.md) · [show-routes-with-outlets.md](references/show-routes-with-outlets.md) · [navigate-to-routes.md](references/navigate-to-routes.md) · [route-guards.md](references/route-guards.md) · [data-resolvers.md](references/data-resolvers.md) · [router-lifecycle.md](references/router-lifecycle.md) · [rendering-strategies.md](references/rendering-strategies.md) · [route-animations.md](references/route-animations.md). Deeper: https://angular.dev/guide/routing

**Styling / animations:** [tailwind-css.md](references/tailwind-css.md) · [angular-animations.md](references/angular-animations.md) · [component-styling.md](references/component-styling.md)

**Testing:** [testing-fundamentals.md](references/testing-fundamentals.md) · [component-harnesses.md](references/component-harnesses.md) · [router-testing.md](references/router-testing.md) · [e2e-testing.md](references/e2e-testing.md)

**Tooling:** [cli.md](references/cli.md) · [migrations.md](references/migrations.md) · [mcp.md](references/mcp.md) · [environment-configuration.md](references/environment-configuration.md)
