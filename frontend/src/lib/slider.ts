/**
 * Slider value model: the thumb moves continuously on 0..100, but an Answer is
 * a discrete 1..5. Each stop sits at the centre of an equal band, so 0..100 maps
 * to the nearest of 5 stops, and each stop maps back to a canonical percent for
 * keyboard jumps and the initial (Neutral) position.
 */

export const STOP_LABELS = [
  'Very inaccurate',
  'Moderately inaccurate',
  'Neutral',
  'Moderately accurate',
  'Very accurate',
] as const

/** Continuous 0..100 -> nearest discrete Answer 1..5. */
export function percentToValue(percent: number): number {
  const clamped = Math.min(100, Math.max(0, percent))
  return Math.round(clamped / 25) + 1
}

/** Discrete Answer 1..5 -> its canonical 0..100 thumb position. */
export function valueToPercent(value: number): number {
  return (value - 1) * 25
}

/** Live label under the slider for a continuous position. */
export function labelForPercent(percent: number): string {
  return STOP_LABELS[percentToValue(percent) - 1]
}

/** Centered Neutral (value 3) — the starting position for each item. */
export const NEUTRAL_PERCENT = valueToPercent(3)
