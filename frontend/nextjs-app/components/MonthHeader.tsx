import styles from "../styles/dashboard.module.css";

interface MonthHeaderProps {
  monthLabel: string;
  onPrev: () => void;
  onNext: () => void;
  onMenu: () => void;
}

export const MonthHeader = ({ monthLabel, onPrev, onNext, onMenu }: MonthHeaderProps) => {
  return (
    <header className={styles.toolbar}>
      <button className={`${styles.iconButton}`} onClick={onPrev} aria-label="Previous month">
        ←
      </button>
      <div className={styles.toolbarTitle}>
        <span className={styles.pageTitle}>Transaction</span>
        <small className={styles.monthLabel}>{monthLabel}</small>
      </div>
      <div className={styles.toolbarActions}>
        <button className={styles.menuButton} onClick={onMenu} aria-label="Open menu">
          ☰
        </button>
        <button className={`${styles.iconButton}`} onClick={onNext} aria-label="Next month">
          →
        </button>
      </div>
    </header>
  );
};
