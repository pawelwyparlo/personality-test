import { labelForPercent } from '../lib/slider'
import styles from './Slider.module.css'

/**
 * Continuous slider on 0..100. The visible track/fill/thumb are drawn under a
 * transparent native range input so keyboard, pointer, and screen-reader support
 * come for free. The parent owns the value (continuous) and maps it to 1..5 on
 * commit; keyboard 1..5 is handled at the page level to jump to stops.
 */
export function Slider({
  percent,
  onChange,
}: {
  percent: number
  onChange: (percent: number) => void
}) {
  const label = labelForPercent(percent)
  return (
    <div className={styles.wrap}>
      <div className={styles.ends}>
        <span>Very inaccurate</span>
        <span>Neutral</span>
        <span>Very accurate</span>
      </div>
      <div className={styles.track}>
        <input
          className={styles.input}
          type="range"
          min={0}
          max={100}
          step={1}
          value={percent}
          onChange={(e) => onChange(Number(e.target.value))}
          aria-label="How accurately does this describe you?"
          aria-valuetext={label}
        />
        <div className={styles.rail} />
        <div className={styles.fill} style={{ width: `${percent}%` }} />
        <div className={styles.ticks}>
          {[0, 1, 2, 3, 4].map((i) => (
            <div key={i} className={styles.tick} />
          ))}
        </div>
        <div className={styles.thumb} style={{ left: `${percent}%` }} />
      </div>
      <div className={styles.liveLabel}>{label}</div>
    </div>
  )
}
