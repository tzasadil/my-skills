# UX/UI Evaluation Framework

Structured framework for evaluating interfaces against research-backed principles. Use when reviewing designs or existing interfaces.

## Smell Taxonomy (8 Antipatterns)

### efficiency

**overloaded-screen**
- Signal: More than 7 distinct action areas visible; users say "where do I start?"
- Fix: Group into 3-5 thematic sections. Surface 5 most critical above fold.

**click-cemetery**
- Signal: Users must click 3+ times for simple task; dead-end paths with no outcome
- Fix: Reduce steps, add shortcuts, ensure every path has an outcome.

### error-prevention

**form-graveyard**
- Signal: More than 10 required fields visible at once; no inline validation; submit-only error display
- Fix: Break into wizard with 4-5 fields per step. Add inline validation on blur.

### feedback

**silent-errors**
- Signal: Errors occur but no message shown; user doesn't know what went wrong
- Fix: Show error messages inline, explain what went wrong and how to fix it.

**dead-end-states**
- Signal: Empty state or error with no action to take; user is stuck
- Fix: Always provide next action. Empty states are invitations, not dead ends.

### learnability

**mystery-navigation**
- Signal: Unclear labels, icon-only navigation with no labels; features users can't find
- Fix: Add text labels under all icons. Test icon recognition (must be 90%+ on first attempt).

### accessibility

**contrast-blindness**
- Signal: Text on background with contrast ratio below 4.5:1; relying on color alone
- Fix: Increase contrast to 4.5:1 minimum. Add icons/labels alongside color.

### consistency

**inconsistent-actions**
- Signal: Same action named differently ("Save" vs "Continue" with no semantic difference); visual styles vary
- Fix: Standardize naming and visual treatment for equivalent actions.

## Severity Guidelines

| Severity | Criteria |
|----------|----------|
| `critical` | Blocks task completion, causes abandonment, or accessibility failure |
| `warning` | Degrades experience, measurably affects conversion or satisfaction |
| `suggestion` | Improvement opportunity; interface works but could be better |

**Always critical:** Contrast blindness, overloaded screen (15+ elements), form graveyard (12+ fields)

## Evaluation Workflow

### Step 1: Classify Interface Type

Identify: `dashboard`, `form`, `onboarding`, `modal`, `navigation`, `settings`, `landing-page`, `checkout`, `empty-state`, `data-table`, `ai-chat`, `mobile-app`, `email`, `documentation`

### Step 2: Extract Signals

Look for:
- Counts (fields, buttons, nav items, steps)
- Labels and copy (button text, nav labels, error messages)
- Layout patterns (above fold, element placement)
- Feedback patterns (what happens after actions)
- Color and contrast
- Mobile vs desktop context

### Step 3: Map to Smells

| Signal Type | Primary Categories |
|-------------|-------------------|
| High element count, density | efficiency |
| Form with many fields | error-prevention |
| Missing feedback | feedback |
| Unclear labels, hidden features | learnability |
| Color mentions, low contrast | accessibility |
| Same action described differently | consistency |

### Step 4: Assign Severity

Use severity guidelines above. A smell is "detected" when 2+ symptoms match or 1 critical symptom matches with high confidence.

### Step 5: Remediate

For each detected smell:
1. State what's violated and why it matters
2. Give concrete fix with measurable outcome
3. Estimate time to fix

## Key Principles Reference

| Part | Domain | Key Principles |
|------|--------|---------------|
| Part 1 | Cognitive Foundations | Cognitive Load, Miller's Law, Chunking, Hick's Law, Working Memory, Serial Position, Peak-End Rule |
| Part 2 | Visual Design | Visual Hierarchy, Gestalt Laws (Proximity, Similarity, Closure, Continuity), Figure-Ground, Contrast, Whitespace |
| Part 3 | Interaction Design | Progressive Disclosure, Fitts's Law, Error Prevention, Feedback Loops, Affordances, Microinteractions |
| Part 4 | Information Architecture | Navigation Patterns, Mental Models, Recognition vs Recall, Wayfinding, Search, Labeling |
| Part 5 | AI and Emerging Interfaces | Conversational Flow, AI Transparency, Cognitive Load Calibration for AI, Automation Bias Prevention |
| Part 6 | Human-Centered Design | Accessibility, Inclusive Design, Trust Signals, Emotional Design, Ethical Patterns |

## Quick Checklist

Before presenting any design, verify:

- [ ] Can users identify primary action in <3 seconds?
- [ ] Are there 7 or fewer distinct action areas?
- [ ] Do forms have 7 or fewer visible fields (or use progressive disclosure)?
- [ ] Is inline validation present on blur?
- [ ] Do error states explain what went wrong AND how to fix?
- [ ] Do empty states provide an action to take?
- [ ] Do navigation items have text labels (not icons only)?
- [ ] Does text meet 4.5:1 contrast ratio?
- [ ] Is color not the only way to convey information?
- [ ] Are equivalent actions named and styled consistently?

## Flow Checklists

Preflight (before design) and postflight (before shipping) checklists for common flow types.

### onboarding

**Preflight Questions:**
- What's the ONE thing users must accomplish?
- How many steps? (3-5 optimal)
- What happens if they abandon halfway?
- What's the success celebration?
- How do they get help?

**Postflight Checks:**
- [ ] Progress indicator visible at all steps
- [ ] Single critical action per step
- [ ] Skip option available
- [ ] Resume capability after abandonment
- [ ] Success celebration on completion

### forms

**Preflight Questions:**
- Which fields are truly required?
- What's the minimum viable data to start?
- When do users see validation feedback?
- What happens on submission success/failure?

**Postflight Checks:**
- [ ] Max 7 visible fields (or progressive disclosure)
- [ ] Inline validation on blur
- [ ] Error messages next to fields
- [ ] Submit button enabled until request starts
- [ ] Clear success/failure feedback

### pricing

**Preflight Questions:**
- How many plans? (3-4 optimal)
- What's the recommended plan?
- What differentiates plans?
- Is annual/monthly toggle needed?

**Postflight Checks:**
- [ ] 3-4 plans max (Hick's Law)
- [ ] Recommended plan highlighted
- [ ] Feature comparison clear
- [ ] CTA on each plan
- [ ] FAQ below pricing

### dashboard

**Preflight Questions:**
- What's the primary metric?
- What actions do users take from here?
- How often do users visit?
- What's the data refresh rate?

**Postflight Checks:**
- [ ] 5-7 KPIs max above fold
- [ ] Grouped into logical sections
- [ ] Drill-down available
- [ ] Loading/empty states for every widget
- [ ] Export/share options

### empty-states

**Preflight Questions:**
- What should users do first?
- What content will appear here?
- How do they get started?

**Postflight Checks:**
- [ ] Illustration or icon
- [ ] Clear headline
- [ ] Description of what will appear
- [ ] Primary action to get started
- [ ] Not broken UI for empty data
