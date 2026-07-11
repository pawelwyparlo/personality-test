import type { ReactNode } from 'react'

import styles from './Placeholder.module.css'

/** Sticker-styled card used as a placeholder for routes built in later PRs. */
export function Placeholder({
  title,
  children,
}: {
  title: string
  children?: ReactNode
}) {
  return (
    <section className={styles.card}>
      <h1>{title}</h1>
      {children}
    </section>
  )
}
