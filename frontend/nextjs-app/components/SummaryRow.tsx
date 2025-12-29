import styles from "../styles/dashboard.module.css";

interface SummaryRowProps {
  totalLabel: string;
  totalValue: string;
  merchantCount: number;
  categoryCount: number;
}

export const SummaryRow = ({
  totalLabel,
  totalValue,
  merchantCount,
  categoryCount,
}: SummaryRowProps) => {
  return (
    <section className={styles.summaryRow}>
      <div>
        <p>{totalLabel}</p>
        <strong>{totalValue}</strong>
      </div>
      <div>
        <p>Merchants</p>
        <strong>{merchantCount}</strong>
      </div>
      <div>
        <p>Categories</p>
        <strong>{categoryCount}</strong>
      </div>
    </section>
  );
};
