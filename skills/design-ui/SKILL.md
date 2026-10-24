---
name: design-ui
description: Use when heavily restyling web components, pages, or applications. Create distinctive, production-grade interfaces with high design quality, not generic AI aesthetics.
---

# Innovative UX Designer

Distinctive production UI. Bold direction, not generic AI aesthetics.

## Before code

Ask, then commit to one extreme. No half measures.

1. **Purpose.** What problem? Who uses it?
2. **Tone.** Pick an extreme below.
3. **Constraints.** Framework, performance, a11y.
4. **Differentiation.** What makes it unforgettable?

Present 2–3 approaches with trade-offs, then implement.

**Tones:** brutally minimal · maximalist chaos · retro-futuristic · organic/natural · luxury/refined · playful/toy-like · editorial/magazine · brutalist/raw · art deco/geometric · soft/pastel · industrial/utilitarian

## Plan

Compact, then build:

- **Color:** 4–6 named hex values
- **Type:** faces for 2+ roles (display, body, utility)
- **Layout:** one-sentence descriptions + ASCII wireframes
- **Signature:** the one thing this page is remembered by

Spend boldness in one place. Quiet everything else. Quality floor without announcing it: responsive to mobile.

If the brief does not pin the subject, pin it: one concrete subject, audience, the page's single job. Distinctive choices come from that world's materials, instruments, artifacts, vernacular. Use the brief's real content.

## Direction

- **Hero is a thesis.** Open with the most characteristic thing: headline, image, animation, live demo, interactive moment. "A big number with a small label, supporting stats, and a gradient accent" is the template answer — only if it is truly the best option.
- **Type carries personality.** Pair display and body on purpose. Scale, weight, width, spacing are part of the design.
- **Structure is information.** Numbering, eyebrows, dividers, labels encode something true. `01/02/03` only when order carries meaning.
- **Motion is deliberate.** One orchestrated moment (load, scroll reveal, hover, ambient) beats scatter. Extra animation reads as AI.
- **Match complexity to vision.** Maximalist needs elaborate execution. Minimal needs precision in spacing, type, detail.

**Principles:** reduce until the simplest effective solution (every element justifies itself) · affordance from color, spacing, type, intentional shadow · hierarchy from type scale, contrast, space · pixel-level detail · every element communicates its function · the technology disappears.

### Never as defaults

**Fonts:** Inter, Roboto, Arial, system fonts as primary, Space Grotesk.

**Colors:** generic SaaS blue (`#3B82F6`), purple gradients on white.

**Effects:** glass morphism, Apple mimicry, liquid/blob backgrounds.

**Layouts:** cookie-cutter component grids, equal generous padding, shadow-as-hierarchy, `rounded-2xl` on everything.

Atmosphere over flat fills: photography, patterns, textures, gradient meshes, noise, geometric pattern, layered transparency, dramatic shadow, decorative border. Custom cursors, grain, contextual effects when they serve the brief.

AI clusters around three looks — legitimate for some briefs, not the free-axis default:

1. Warm cream (`~#F4F1EA`) + high-contrast serif display + terracotta
2. Near-black + one acid-green or vermilion accent
3. Broadsheet: hairline rules, zero radius, dense newspaper columns

Brief pins a direction -> follow it. Axis left free -> do not spend it on those three.

Inspiration: modern landing pages (Perplexity, Comet, Dia), Framer templates, brand studios, Bauhaus / Otl Aicher / Braun, slow looping CSS/SVG backgrounds.

## Color

Two roles:

1. **Neutral (4–5):** background (lightest), surface, border, text (darkest). Slightly desaturated warm or cool greys.
2. **Accent (1–3):** primary CTA, status, focus/hover.

- Background = lightest neutral. Primary text = darkest. Secondary = mid-tone.
- Primary button: accent + white text. Secondary: neutral + border + dark text.
- Hover darken 10–15%. Focus ring in accent. Disabled 40–50% opacity.
- Unexpected neutrals: warm grey, soft off-white, deep charcoal. Sharp accents: terracotta+charcoal, sage+navy, coral+slate. Dominant + sharp beats timid.

## Type

- Display: emotion. Body: legibility. UI/labels: scan.
- 2–3 typefaces max, characterful. 3 weights per face (400/500/700). Variable fonts when useful.
- Scale (1.25x): `xs 0.64rem` · `sm 0.8rem` · `base 1rem` · `lg 1.25rem` · `xl 1.563rem` · `2xl 1.953rem` · `3xl 2.441rem` · `4xl 3.052rem` · `5xl 3.815rem`
- Body line-height 1.5. Line length 45–75ch. Tracking tighter on large, looser on small.
- Pairings: serif+sans · geometric+humanist · display+system.
- `…` not `...`. Curly quotes. Non-breaking spaces: `10&nbsp;MB`, `⌘&nbsp;K`. Loading strings end with `…`. `font-variant-numeric: tabular-nums` on number columns. `text-wrap: balance` or `text-pretty` on headings.

## Forms

- `autocomplete` + meaningful `name`. Correct `type` / `inputmode`.
- Never block paste. Labels clickable (`htmlFor` or wrap).
- `spellCheck={false}` on emails, codes, usernames.
- Checkbox/radio: label + control share one hit target.
- Submit stays enabled until the request starts; spinner during.
- Errors inline; focus first error on submit.
- Placeholders end with `…` and show an example.
- Warn before leaving unsaved changes.

## Content and layout

- Long text: `truncate`, `line-clamp-*`, or `break-words`. Flex children that truncate need `min-w-0`.
- Empty states: do not render broken UI for empty strings/arrays. Anticipate short, average, and very long user input.
- Grid/flex wrappers with `gap`. Wrappers over child margins. Group by proximity. Hierarchy via size, color, spacing.
- Full-bleed: `env(safe-area-inset-*)`. Stop unwanted scrollbars. Flex/grid over JS measurement.

## Motion

| Easing      | CSS                                      | Use           |
| ----------- | ---------------------------------------- | ------------- |
| Ease-out    | `cubic-bezier(0.0, 0.0, 0.2, 1)`         | Entrances     |
| Ease-in     | `cubic-bezier(0.4, 0.0, 1, 1)`           | Exits         |
| Ease-in-out | `cubic-bezier(0.4, 0.0, 0.2, 1)`         | State changes |
| Spring      | `cubic-bezier(0.68, -0.55, 0.265, 1.55)` | Playful       |

| Weight   | Duration | Examples                  |
| -------- | -------- | ------------------------- |
| Light    | 150ms    | Icons, badges, chips      |
| Standard | 300ms    | Cards, panels, list items |
| Weighty  | 500ms    | Modals, page transitions  |

- Animate only `transform` and `opacity`. Never `transition: all`. Set `transform-origin`. UI under 500ms. Interruptible. Do not delay the user's next action. Respect `prefers-reduced-motion`.
- `touch-action: manipulation`. Set `-webkit-tap-highlight-color`. `overscroll-behavior: contain` in overlays. During drag: no text select, `inert` on dragged nodes. `autoFocus` desktop only, one primary input; never on mobile.

## Navigation and UX

- Links are `<a>`/`<Link>` (Cmd/Ctrl+click, middle-click). Deep-link stateful UI.
- Destructive: confirm or undo. Never immediate.
- Direct manipulation. Feedback within 100ms. Similar look -> similar behavior. Progressive disclosure.
- Command palettes, smart search. Time-based dark mode, device-based simplification OK. Shadows/gradients when intentional.

**Skeletons for content, not spinners:**

```tsx
// use as a content loading placeholder
function TaskListSkeleton() {
  return (
    <div className="space-y-3" aria-busy="true" aria-label="Loading tasks">
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="h-12 bg-muted animate-pulse rounded" />
      ))}
    </div>
  );
}
```

Optimistic update: paint immediately, rollback on error.

## Implement

- Prefer shadcn v4 (`@/components/ui`). Tailwind utilities only. `@phosphor-icons/react`. `sonner` for toasts. Loading states always.

```
src/components/
  TaskList/
    TaskList.tsx
    TaskList.test.tsx
    use-task-list.ts
    types.ts
```

Composition over config. Data fetching in a container; presentation dumb.

```tsx
// use as container vs presentation split
function TaskListContainer() {
  const { tasks, isLoading, error, refetch } = useTasks();
  if (isLoading) return <TaskListSkeleton />;
  if (error) return <ErrorState message="Failed to load" retry={refetch} />;
  if (tasks.length === 0) return <EmptyState message="No tasks yet" />;
  return <TaskList tasks={tasks} />;
}

function TaskList({ tasks }: { tasks: Task[] }) {
  return (
    <ul role="list" className="divide-y">
      {tasks.map((t) => (
        <TaskItem key={t.id} task={t} />
      ))}
    </ul>
  );
}
```

| State                     | Use                              |
| ------------------------- | -------------------------------- |
| `useState`                | Component-local UI               |
| Lifted                    | 2–3 siblings                     |
| Context                   | Theme, auth, locale (read-heavy) |
| URL `searchParams`        | Filters, pagination, shareable   |
| Server (React Query, SWR) | Remote + cache                   |
| Global (Zustand, Redux)   | Complex app-wide client          |

No prop drilling past 3 levels. Conditional class via ternary or clsx. Watch colliding utilities (especially section padding).

## Performance, theme, i18n

- Lists >50: virtualize (`virtua`, `content-visibility: auto`).
- No layout reads in render (`getBoundingClientRect`, `offsetHeight`, `offsetWidth`, `scrollTop`). Batch DOM reads/writes.
- Prefer uncontrolled inputs; controlled must be cheap per keystroke.
- `<link rel="preconnect">` for CDNs. Critical fonts: `<link rel="preload" as="font">` + `font-display: swap`.
- Dark: `color-scheme: dark` on `<html>`. `<meta name="theme-color">` matches background. Native `<select>` needs explicit `background-color` and `color`.
- Dates: `Intl.DateTimeFormat`. Numbers/currency: `Intl.NumberFormat`. Language from `Accept-Language` / `navigator.languages`, not IP. Brand names, code, ids: `translate="no"`.
- Controlled inputs need `onChange` (or `defaultValue`). Guard date/time against hydration mismatch. `suppressHydrationWarning` only when required.

## Breakpoints

| Range | px        | Strategy                   |
| ----- | --------- | -------------------------- |
| XS    | 0–479     | Single column, stacked nav |
| SM    | 480–767   | Single column, bottom nav  |
| MD    | 768–1023  | 2 columns, sidebar nav     |
| LG    | 1024–1439 | Multi-column, full nav     |
| XL    | 1440+     | Max-width containers       |

Fluid type: `h1 { font-size: clamp(2rem, 5vw, 4rem); }`. Touch targets ≥44×44px.

## Accessibility

WCAG 2.1 AA. Keyboard for every control. Semantic HTML. Alt text. Visible focus. Logical tab order. `aria-label` / `role` when the element is not already named. No `user-scalable=no` / `maximum-scale=1`. No `outline-none` without a `:focus-visible` replacement.

## Copy

Words are design material. Name by what the person controls, not the system. Specific over clever. Active voice: "Save changes" not "Submit". Same action name through the flow (`Publish` -> toast `Published`). Errors: what broke and how to fix; no apology. Empty states invite an action. One job per element.

- Title Case headings/buttons (Chicago). Numerals: `8 deployments`. Specific buttons: `Save API Key` not `Continue`. Second person. `&` where space is tight.

## AI surfaces

| Axis       | Check                       |
| ---------- | --------------------------- |
| Disclosure | AI nature is visible        |
| Override   | User can correct output     |
| Accuracy   | Confidence shown            |
| Consent    | Data use for AI is explicit |

Frame as suggestion, not fact. Cite factual claims. Preview irreversible actions (delete, send, purchase, publish). Missing preview -> critical.

Review pass: [CODE-REVIEW.md](CODE-REVIEW.md). Component-type mapping: [COMPONENTS.md](COMPONENTS.md). Smell taxonomy when evaluating: [EVALUATION.md](EVALUATION.md). React/Next perf: [REACT-PERFORMANCE.md](REACT-PERFORMANCE.md).
