---
name: editing-ui
description: Use when changing or reviewing user-facing UI code (pages, components, styles, UI copy). Not for a new visual direction or a heavy restyle (see design-ui).
---

# Editing UI

Rules for every UI change, in every project. Project rules (`AGENTS.md`) win on conflict. Review: a broken rule is a finding.

## Consistency

- Extract shared components and reuse them aggressively -> pages stay visually consistent.
- Same job -> same component and same interaction on every page (edit, download, filter, upload). Table columns align. Filter fields share one width.
- A reference to another record (contract, company, order) is a link to it everywhere it shows, never plain text.
- A row, card line or tile that opens one target is one link or button over its whole area: label, pill and value together. Never a tiny link beside an unclickable label.

## Density and layout

- App screens (dashboard, admin, settings, form, tool): dense, never small. No big gaps, no filler or decorative elements, more information per screen. Text and click targets stay large (body text 16px or more, controls 40px or taller) => easy for older users.
- Modals are big by default (most of the page). Never scale one down because its content is small. Exception: a confirm dialog stays small. A list inside a modal uses short pages, not a long scroll.
- A control that commonly shows up and disappears reserves its space (invisible, not removed) => no layout shift.
- File drop targets are generous: the whole page by default, split into one region per drop area when a page has several independent ones. The field itself stays compact (a choose button and a short drag hint, no big drop box). While files are dragged, the target shows a dashed frame. Dragged text or links open nothing.

## Text

- UI copy: short label and bare value, not sentences. Cut caveats, mechanics, and technical detail.
- No redundant text when the behavior is clear without it: no label that repeats its container or page title, no value shown twice, no success message for a change the user already sees. Prefer visual cues, then hover text or an (i) icon.
- Text never contradicts behavior: a hint that states a limit (minimum characters, maximum files, maximum length) matches the code, and the control enforces it.
- Multi-language app: every visible string is translated in every locale, including browser-native control text (file input), API error text, and static pages. One word per thing across button, page title, and menu.

## Editing and saving

- A record's Edit button sits top right, above the details it edits. In edit mode, Save and Cancel take its place. Never below the table.
- One save button: disabled when nothing changed.
- Two steps (save draft -> publish): the buttons are mutually exclusive.
  - Pending changes -> Save draft enabled, Publish disabled.
  - No pending changes -> Publish enabled, Save draft disabled.

## Lists and search

- Every list has a logical default sort order. Always. No list renders in storage or insertion order. Time-based records: newest first. Tiles count as a list. A table shows its sort column on load.
- A list that can outgrow one page has filters and paging. Each active filter has its own clear control.
- Search ignores diacritics. Import is locale aware (decimal dot or comma).
- Every table has clickable column headers that sort by that column. First click ascending, second click reverses. A paged list sorts in the API across all pages, never only the rows on screen. Action and multi-value columns stay plain.
- List filters, sort and page live in the session per page path, never in the URL query, through one shared hook (`usePageFilters`). One zod schema per page, read on the server. Text filters save debounced and on blur. Selects, sort and page save at once. Any filter change resets to page 1. No Filter button. A link that arrives with URL filters seeds the session once, then redirects to the clean path.

## Emphasis and color

- Visual weight follows urgency. Danger and items that need action are the loudest thing in their row. Routine or finished states are small quiet text. Selected, unread, and new are obvious at a glance. Never color alone: pair it with text or an icon.
- Chrome (shell, navigation, headings, buttons, decoration) uses the project palette only. Page content uses color where it carries meaning: status, category, file type, charts, avatars. There, colored beats grey. No color as decoration. Keep text contrast at 4.5:1 or higher.

## State and feedback

- Newest async result wins. A stale response never overwrites newer state.
- Awaited actions leave their busy state on failure or timeout.
- Failures show the client's own copy. Raw transport, HTML, or parser error text never reaches the user.
- Confirmation popup for destructive actions.

## Accessibility

- Disabled controls explain why on hover and on keyboard focus. Native `disabled` swallows both: wrap the control or use `aria-disabled`.
- Async changes and errors announce through an always-mounted live region. A region mounted with its content is not announced reliably. Errors use `role="alert"`.
- Focus moves to a stable target when the focused control unmounts or is replaced (Add, Remove, Retry, dialog close). It never drops to the page body.
