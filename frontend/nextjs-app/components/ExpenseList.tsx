import { Expense } from "../types/expense";
import { formatAmount } from "../utils/format";
import styles from "../styles/dashboard.module.css";

interface ExpenseListProps {
  groupedExpenses: Array<[string, Expense[]]>;
  fallbackCurrency: string;
  onEdit: (expense: Expense) => void;
  loading: boolean;
  error: string | null;
}

export const ExpenseList = ({
  groupedExpenses,
  fallbackCurrency,
  onEdit,
  loading,
  error,
}: ExpenseListProps) => {
  return (
    <section className={styles.listCard}>
      {error && <p className={styles.error}>{error}</p>}
      {loading ? (
        <div className={styles.empty}>Loading your expenses…</div>
      ) : groupedExpenses.length === 0 ? (
        <div className={styles.empty}>
          Nothing to show yet. Send a receipt via WhatsApp to see it here.
        </div>
      ) : (
        groupedExpenses.map(([day, items]) => (
          <div className={styles.dayGroup} key={day}>
            <div className={styles.dayHeader}>
              <div>
                <span className={styles.dayNumber}>{new Date(day).getDate()}</span>
                <span className={styles.dayDate}>
                  {new Date(day).toLocaleDateString(undefined, {
                    year: "numeric",
                    month: "2-digit",
                  })}
                </span>
              </div>
              <span className={styles.dayTotal}>
                {formatAmount(
                  items.reduce((sum, item) => sum + item.amount, 0),
                  items[0]?.currency || fallbackCurrency
                )}
              </span>
            </div>
            {items.map((expense) => (
              <div className={styles.expenseRow} key={expense.id}>
                <div>
                  <p className={styles.expenseTitle}>
                    {expense.merchant || "Expense"}
                  </p>
                  <span className={styles.expenseMeta}>
                    {expense.category || "General"} · {expense.notes || "—"}
                  </span>
                </div>
                <div className={styles.expenseActions}>
                  <span className={styles.expenseAmount}>
                    {formatAmount(expense.amount, expense.currency)}
                  </span>
                  <button className={styles.linkBtn} onClick={() => onEdit(expense)}>
                    Edit
                  </button>
                </div>
              </div>
            ))}
          </div>
        ))
      )}
    </section>
  );
};
