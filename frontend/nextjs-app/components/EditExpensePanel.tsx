import { FormEvent } from "react";

import { Expense } from "../types/expense";
import styles from "../styles/dashboard.module.css";

interface EditExpensePanelProps {
  editing: Expense | null;
  form: {
    amount: string;
    currency: string;
    category: string;
    merchant: string;
    notes: string;
    expense_date: string;
  };
  onChange: (next: EditExpensePanelProps["form"]) => void;
  onCancel: () => void;
  saving: boolean;
  error: string | null;
  onSubmit: (event: FormEvent) => void;
}

export const EditExpensePanel = ({
  editing,
  form,
  onChange,
  onCancel,
  saving,
  error,
  onSubmit,
}: EditExpensePanelProps) => {
  if (!editing) return null;
  return (
    <section className={styles.editPanel} aria-label="Edit expense">
      <div className={styles.editHeader}>
        <button className={styles.ghostBtn} onClick={onCancel}>
          ←
        </button>
        <div>
          <p>Edit transaction</p>
        </div>
        <span className={styles.editSpacer} />
      </div>
        <form className={styles.editList} onSubmit={onSubmit}>
          <div className={styles.editRow}>
            <span>Date</span>
            <input
              type="date"
              value={form.expense_date}
              onChange={(e) => onChange({ ...form, expense_date: e.target.value })}
              required
            />
          </div>
        <div className={styles.editRow}>
          <span>Category</span>
          <input
            type="text"
            value={form.category}
            onChange={(e) => onChange({ ...form, category: e.target.value })}
          />
        </div>
        <div className={styles.editRow}>
          <span>Merchant</span>
          <input
            type="text"
            value={form.merchant}
            onChange={(e) => onChange({ ...form, merchant: e.target.value })}
          />
        </div>
        <div className={styles.editRow}>
          <span>Amount</span>
          <div className={styles.amountGroup}>
            <input
              type="text"
              value={form.currency}
              onChange={(e) => onChange({ ...form, currency: e.target.value })}
              className={styles.currencyInput}
              required
            />
            <input
              type="number"
              step="0.01"
              value={form.amount}
              onChange={(e) => onChange({ ...form, amount: e.target.value })}
              required
            />
          </div>
        </div>
          <div className={styles.editRow}>
            <span>Note</span>
            <input
              type="text"
              value={form.notes}
              onChange={(e) => onChange({ ...form, notes: e.target.value })}
            />
          </div>
          {error && <p className={styles.editError}>{error}</p>}
        <div className={styles.editActions}>
          <button type="button" className={styles.ghostBtn} onClick={onCancel} disabled={saving}>
            Back
          </button>
          <button type="submit" className={styles.primaryBtn} disabled={saving}>
            {saving ? "Updating…" : "Update"}
          </button>
        </div>
        </form>
      </section>
  );
};
