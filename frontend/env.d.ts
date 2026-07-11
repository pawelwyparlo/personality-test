/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_TEST_MODE?: string
  readonly VITE_CLERK_PUBLISHABLE_KEY?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
