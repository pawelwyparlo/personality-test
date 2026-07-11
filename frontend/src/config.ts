/** Dev-only testing controls are exposed when VITE_TEST_MODE === "true". */
export const TEST_MODE = import.meta.env.VITE_TEST_MODE === 'true'

/**
 * The Clerk publishable key, if configured. The coach account gate (ADR-0002)
 * only mounts Clerk when this is present — everything before the gate works with
 * no keys at all, and the coach intro degrades to a setup notice keyless.
 */
export const CLERK_PUBLISHABLE_KEY =
  import.meta.env.VITE_CLERK_PUBLISHABLE_KEY ?? ''

/** True when Clerk is configured, so ClerkProvider and its components mount. */
export const clerkEnabled = CLERK_PUBLISHABLE_KEY.length > 0
