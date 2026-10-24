# React/Next.js Performance Guide

From Vercel Engineering. 70 rules across 8 categories, prioritized by impact.

## Priority 1: Eliminating Waterfalls (CRITICAL)

### Promise.all() for Independent Operations
```typescript
// Bad: sequential, 3 round trips
const user = await fetchUser()
const posts = await fetchPosts()
const comments = await fetchComments()

// Good: parallel, 1 round trip
const [user, posts, comments] = await Promise.all([
  fetchUser(), fetchPosts(), fetchComments()
])
```

### Defer Await Until Needed
```typescript
// Bad: blocks both branches
const userData = await fetchUserData(userId)
if (skipProcessing) return { skipped: true }

// Good: only blocks when needed
if (skipProcessing) return { skipped: true }
const userData = await fetchUserData(userId)
```

### Start Promises Early, Await Late
```typescript
// Bad: config waits for auth
const session = await auth()
const config = await fetchConfig()
const data = await fetchData(session.user.id)

// Good: auth and config start immediately
const sessionPromise = auth()
const configPromise = fetchConfig()
const session = await sessionPromise
const [config, data] = await Promise.all([configPromise, fetchData(session.user.id)])
```

### Strategic Suspense Boundaries
```tsx
// Bad: entire page waits for data
async function Page() {
  const data = await fetchData()
  return <div><Sidebar /><DataDisplay data={data} /></div>
}

// Good: wrapper shows immediately, data streams in
function Page() {
  return (
    <div>
      <Sidebar />
      <Suspense fallback={<Skeleton />}>
        <DataDisplay />
      </Suspense>
    </div>
  )
}
```

## Priority 2: Bundle Size (CRITICAL)

### Avoid Barrel Imports
```typescript
// Bad: loads 1,583 modules
import { Check, X, Menu } from 'lucide-react'

// Good (Next.js 13.5+): keeps standard imports, transforms automatically
import { Check, X, Menu } from 'lucide-react'

// Good (non-Next.js): direct imports
import Button from '@mui/material/Button'
```

### Dynamic Imports for Heavy Components
```typescript
// Bad: Monaco bundles with main chunk ~300KB
import { MonacoEditor } from './monaco-editor'

// Good: loads on demand
const MonacoEditor = dynamic(() => import('./monaco-editor'), { ssr: false })
```

### Defer Third-Party After Hydration
```typescript
// Bad: blocks initial bundle
import { Analytics } from '@vercel/analytics/react'

// Good: loads after hydration
const Analytics = dynamic(() => import('@vercel/analytics/react'), { ssr: false })
```

### Preload on User Intent
```typescript
// Preload on hover/focus
<button
  onMouseEnter={() => void import('./monaco-editor')}
  onFocus={() => void import('./monaco-editor')}
  onClick={openEditor}
>
  Open Editor
</button>
```

## Priority 3: Server-Side (HIGH)

### Authenticate Server Actions
```typescript
// Bad: anyone can call this
'use server'
export async function deleteUser(userId: string) {
  await db.user.delete({ where: { id: userId } })
}

// Good: auth inside the action
'use server'
export async function deleteUser(userId: string) {
  const session = await verifySession()
  if (!session) throw unauthorized()
  if (session.user.id !== userId) throw unauthorized()
  await db.user.delete({ where: { id: userId } })
}
```

### Parallel Data Fetching with Composition
```tsx
// Bad: Sidebar waits for Page's fetch
export default async function Page() {
  const header = await fetchHeader()
  return <div><div>{header}</div><Sidebar /></div>
}

// Good: both fetch simultaneously
async function Header() {
  const data = await fetchHeader()
  return <div>{data}</div>
}
async function Sidebar() {
  const items = await fetchSidebarItems()
  return <nav>{items.map(renderItem)}</nav>
}
export default function Page() {
  return <div><Header /><Sidebar /></div>
}
```

### Minimize Serialization at RSC Boundaries
```tsx
// Bad: serializes all 50 fields
async function Page() {
  const user = await fetchUser()
  return <Profile user={user} />
}

// Good: serializes only needed fields
async function Page() {
  const user = await fetchUser()
  return <Profile name={user.name} />
}
```

### Hoist Static I/O to Module Level
```typescript
// Bad: reads font on every request
export async function GET() {
  const font = await fetch('./fonts/Inter.ttf').then(r => r.arrayBuffer())
}

// Good: loads once at module init
const fontPromise = fetch('./fonts/Inter.ttf').then(r => r.arrayBuffer())
export async function GET() {
  const font = await fontPromise
}
```

### Use after() for Non-Blocking Operations
```typescript
// Bad: logging blocks response
await logUserAction({ userAgent })

// Good: non-blocking
after(async () => {
  await logUserAction({ userAgent })
})
```

## Priority 4: Client-Side (MEDIUM-HIGH)

### Use SWR for Deduplication
```typescript
// Bad: no deduplication
const [users, setUsers] = useState([])
useEffect(() => { fetch('/api/users').then(r => r.json()).then(setUsers) }, [])

// Good: multiple instances share one request
const { data: users } = useSWR('/api/users', fetcher)
```

### Passive Event Listeners
```typescript
// Bad: blocks scrolling
document.addEventListener('touchstart', handleTouch)

// Good: immediate scrolling
document.addEventListener('touchstart', handleTouch, { passive: true })
```

## Priority 5: Re-render (MEDIUM)

### Derive State During Render
```typescript
// Bad: redundant state and effect
const [fullName, setFullName] = useState('')
useEffect(() => { setFullName(firstName + ' ' + lastName) }, [firstName, lastName])

// Good: derive during render
const fullName = firstName + ' ' + lastName
```

### Don't Define Components Inside Components
```typescript
// Bad: recreated every render
function Parent() {
  const Child = () => <div>Hi</div>
  return <Child />
}

// Good: stable reference
const Child = () => <div>Hi</div>
function Parent() {
  return <Child />
}
```

### Use Functional setState
```typescript
// Bad: depends on external count
const increment = () => setCount(count + 1)

// Good: stable callback
const increment = () => setCount(prev => prev + 1)
```

### Lazy State Initialization
```typescript
// Bad: runs on every render
const [state, useState(expensiveComputation())]

// Good: runs only once
const [state, useState(() => expensiveComputation())]
```

### Transitions for Non-Urgent Updates
```typescript
// Bad: blocks input
setSearchQuery(value)

// Good: keeps input responsive
startTransition(() => setSearchQuery(value))
```

## Priority 6: Rendering (MEDIUM)

### Hoist Static JSX
```tsx
// Bad: recreated every render
function Component() {
  return <div className="static"><HeavyComponent /></div>
}

// Good: created once
const staticJSX = <div className="static"><HeavyComponent /></div>
function Component() {
  return staticJSX
}
```

### Explicit Conditional Rendering
```tsx
// Bad: renders 0 or empty string
{items.length && <List items={items} />}

// Good: explicit ternary
{items.length ? <List items={items} /> : null}
```

### content-visibility for Long Lists
```css
.list-item { content-visibility: auto; contain-intrinsic-size: 0 50px; }
```

## Quick Reference

| Category | Impact | Key Rules |
|----------|--------|-----------|
| Waterfalls | CRITICAL | Promise.all, defer await, start early, Suspense |
| Bundle | CRITICAL | No barrels, dynamic imports, defer 3rd party |
| Server | HIGH | Auth actions, parallel fetch, minimize serialization |
| Client | MEDIUM-HIGH | SWR, passive listeners |
| Re-render | MEDIUM | Derive state, functional setState, transitions |
| Rendering | MEDIUM | Hoist JSX, explicit conditionals, content-visibility |
| JS | LOW-MEDIUM | Cache loops, Set/Map lookups, early returns |
