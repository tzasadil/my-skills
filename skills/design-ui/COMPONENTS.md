# Component Type Registry

Map component requests to UX principles. Use when building UI components to ensure research-backed patterns are applied.

## Registry

| Component Type | Primary Principles | Secondary Principles |
|---|---|---|
| `multi-step-form` | cognitive-load, progressive-disclosure | error-prevention-in-forms |
| `form` | cognitive-load, error-prevention-in-forms | fitts-law |
| `data-table` | cognitive-load, hicks-law | visual-hierarchy |
| `dashboard` | cognitive-load, hicks-law | visual-hierarchy |
| `navigation` | hicks-law, recognition-rather-than-recall | mental-model |
| `mobile-nav` | hicks-law, fitts-law | recognition-rather-than-recall |
| `checkout` | cognitive-load, progressive-disclosure | fitts-law |
| `settings` | progressive-disclosure, recognition-rather-than-recall | cognitive-load |
| `onboarding` | cognitive-load, progressive-disclosure | fitts-law |
| `modal` | cognitive-load, fitts-law | progressive-disclosure |
| `empty-state` | progressive-disclosure, mental-model | cognitive-load |
| `landing-page` | visual-hierarchy, fitts-law | serial-position-effect |
| `pricing-page` | visual-hierarchy, hicks-law | serial-position-effect |
| `ai-chat` | conversational-flow, ai-transparency | ai-accuracy-communication |
| `search` | recognition-rather-than-recall, mental-model | cognitive-load |
| `notification` | cognitive-load, fitts-law | progressive-disclosure |

## Key Principles Quick Reference

| Principle | What It Means |
|---|---|
| **Cognitive Load** | Working memory holds 7±2 elements. Break complex interfaces into digestible chunks. |
| **Hick's Law** | Each additional choice increases decision time logarithmically. Reduce visible options. |
| **Fitts's Law** | Time to reach a target is a function of distance and size. Make CTAs large and close. |
| **Progressive Disclosure** | Reveal information incrementally. Show essentials first, details on demand. |
| **Visual Hierarchy** | Guide eye through intentional size, color, contrast, and spacing relationships. |
| **Recognition vs Recall** | Making options visible is easier than requiring memory. Show, don't ask users to remember. |
| **Mental Model** | Match interface structure to user expectations. Use familiar patterns. |
| **Serial Position** | Users remember first and last items best. Put important actions at start/end. |
| **Error Prevention** | Prevent errors before they occur. Validate inline, disable invalid actions. |

## UX Guardrails per Component

When building these components, enforce these non-negotiable rules:

### forms / multi-step-form
- Max 4-5 fields per step (or 7 visible fields on single page)
- Inline validation on blur, not just on submit
- Error messages inline, next to the field
- Submit button stays enabled until request starts

### data-table
- Max 7 visible columns (hide secondary in column picker)
- Row actions in kebab menu, not inline buttons
- Pagination with explicit count ("1-25 of 150"), not infinite scroll
- Sticky header for scroll context

### dashboard
- Max 5-7 KPI cards above fold
- Group related metrics into sections
- Provide drill-down, not all data at once
- Empty/loading states for every widget

### navigation
- Max 5-7 primary items
- Text labels, not icons only
- Current page highlighted
- Mobile: hamburger or bottom nav, not both

### settings
- One section visible at a time (sidebar or tabs)
- Current state immediately visible
- Destructive actions at bottom with visual separation
- Auto-save toggles, explicit save for forms

### onboarding
- Single critical action per step
- Progress indicator visible at all steps
- Allow skip/resume
- Celebrate completion

### modal
- Single primary action
- Close via X, ESC, and outside click
- Trap focus inside
- Restore focus on close

### empty-state
- Illustration or icon + headline + description
- Primary action to get started
- Don't show broken UI for empty data

### landing-page
- Hero = most characteristic thing, not template
- One primary CTA above fold
- Social proof near CTA
- Clear value proposition in <5 seconds

### pricing-page
- 3-4 plans max (Hick's Law)
- Recommended plan highlighted
- Feature comparison table
- Annual/monthly toggle

### ai-chat
- Clear AI disclosure
- Confidence indicators on responses
- Easy correction/feedback mechanism
- Conversation history accessible

### search
- Autocomplete/suggestions
- Recent searches
- Clear empty results state
- Filter options visible

## Prompt Quality Standards

When generating components, prompts should include:

1. **Role line**: "You are an expert [role] specializing in [domain]."
2. **Create statement**: "Create a [component] that [UX outcome]: [research finding]."
3. **Requirements block**: Min 5 bulleted requirements:
   - One count-based rule (e.g., "max 5-7 visible columns")
   - Tech stack call (if specified)
   - One accessibility requirement
   - One responsive behavior requirement
4. **Constraints block**: 2-3 hard constraints:
   - Line count constraint
   - "Don't modify other files"
   - Scope boundary
