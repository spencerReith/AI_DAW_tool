# Plan: Enter Key Triggers "Go" on Launch Page

## Goal
When the user presses Enter on the launch page, it should behave the same as clicking the "go" button.

## Constraint
The "go" button only appears after the ASCII art animation finishes (`done === true`). Enter should only fire `onGo` if `done` is true — pressing Enter during the animation should do nothing.

## Change
**File:** `frontend/src/App.jsx` — `LaunchPage` component

Add a `keydown` event listener in a `useEffect` that calls `onGo()` when `event.key === 'Enter'` and `done === true`.

```js
useEffect(() => {
  function handleKey(e) {
    if (e.key === 'Enter' && done) onGo();
  }
  window.addEventListener('keydown', handleKey);
  return () => window.removeEventListener('keydown', handleKey);
}, [done, onGo]);
```

The dependency on `done` ensures the handler always sees the latest value. Cleanup on unmount prevents leaks.

## Steps
1. In `LaunchPage`, add the `useEffect` above after the existing animation `useEffect`.

## Testing
- Load the app, wait for animation to finish, press Enter — should route to generator.
- Press Enter *during* the animation — should do nothing.
