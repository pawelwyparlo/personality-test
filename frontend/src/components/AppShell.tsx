import { NavLink, Outlet } from 'react-router'

import styles from './AppShell.module.css'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive ? `${styles.navLink} ${styles.navLinkActive}` : styles.navLink

export function AppShell() {
  return (
    <div className={styles.shell}>
      <header className={styles.nav}>
        <div className={styles.navInner}>
          <NavLink to="/" className={styles.wordmark}>
            Big Five
          </NavLink>
          <nav className={styles.links}>
            <NavLink to="/test" className={navLinkClass}>
              Test
            </NavLink>
            <NavLink to="/coach" className={navLinkClass}>
              Coach
            </NavLink>
          </nav>
        </div>
      </header>
      <main className={styles.content}>
        <Outlet />
      </main>
    </div>
  )
}
