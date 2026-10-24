# Signal templates

Copy when persisting a signal to `localStorage`, or when an API needs `.set()` / `.update()` but the state lives behind a getter/setter (signal store field, form model). Call `syncToLocalStorage` from an injection context (`constructor`, field initializer).

`parse` is the storage boundary. JSON load failures drop the key, then the first persist stores a clean default. A successful load skips that first persist so a stale default cannot clobber storage.

## `projectedSignal`

```ts
// use to adapt a getter/setter pair to a settable signal
import { computed, type Signal } from '@angular/core';

export interface SettableSignal<T> {
  (): T;
  set(value: T): void;
  update(updateFn: (value: T) => T): void;
  asReadonly(): Signal<T>;
}

export const projectedSignal = <T>(
  getter: () => T,
  setter: (value: T) => void,
): SettableSignal<T> => {
  const source: Signal<T> = computed(getter);
  return Object.assign(() => source(), {
    set: (value: T): void => setter(value),
    update: (updateFn: (value: T) => T): void => setter(updateFn(source())),
    asReadonly: (): Signal<T> => source,
  });
};
```

## `syncToLocalStorage`

```ts
// use to load then persist a settable signal as JSON in localStorage
import { effect } from '@angular/core';
import type { SettableSignal } from './projected-signal';

const readItem = (key: string): string | null => {
  try {
    return globalThis.localStorage.getItem(key);
  } catch {
    return null;
  }
};

const writeItem = (key: string, value: string): void => {
  try {
    globalThis.localStorage.setItem(key, value);
  } catch {
    // quota / private mode -> skip persist
  }
};

const removeItem = (key: string): void => {
  try {
    globalThis.localStorage.removeItem(key);
  } catch {
    // same Storage failures as read/write
  }
};

type JsonParse = { readonly ok: true; readonly value: unknown } | { readonly ok: false };

const parseJson = (raw: string): JsonParse => {
  try {
    return { ok: true, value: JSON.parse(raw) as unknown };
  } catch {
    return { ok: false };
  }
};

export const syncToLocalStorage = <T>(
  key: string,
  value: SettableSignal<T>,
  parse: (raw: unknown) => T,
  delayMs = 0,
): void => {
  const stored = readItem(key);
  let skipFirstWrite = false;

  if (stored !== null) {
    const parsed = parseJson(stored);
    if (!parsed.ok) {
      removeItem(key);
    } else {
      skipFirstWrite = true;
      value.set(parse(parsed.value));
    }
  }

  effect((onCleanup) => {
    const data = value();
    if (skipFirstWrite) {
      skipFirstWrite = false;
      return;
    }

    const persist = (): void => writeItem(key, JSON.stringify(data));
    if (delayMs <= 0) {
      persist();
      return;
    }

    const timer = setTimeout(persist, delayMs);
    onCleanup(() => clearTimeout(timer));
  });
};
```

## Wire-up

```ts
// use to persist a real WritableSignal
syncToLocalStorage('selected-language', language, LanguageSchema.parse);

// use to persist a store field (or any getter/setter) through the adapter
syncToLocalStorage(
  'project',
  projectedSignal(
    () => store.project(),
    (project) => patchState(store, { project }),
  ),
  ProjectSchema.parse,
);

// use to persist and run a side effect in the same setter
const persistedTheme = projectedSignal(
  () => theme(),
  (next) => {
    theme.set(next);
    paint(next);
  },
);
syncToLocalStorage('theme', persistedTheme, parseTheme);
```

`delayMs` > 0 coalesces writes; the timer is cleared on the next run and on destroy. Browser only. No SSR memory fallback in this helper -> skip the call on the server, or gate reads with `isPlatformBrowser`.
