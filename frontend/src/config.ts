/** Dev-only testing controls are exposed when VITE_TEST_MODE === "true". */
export const TEST_MODE = import.meta.env.VITE_TEST_MODE === 'true'
