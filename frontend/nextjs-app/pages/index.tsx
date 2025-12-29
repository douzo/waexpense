import { FormEvent, useCallback, useEffect, useMemo, useRef, useState } from "react";

import { EditExpensePanel } from "../components/EditExpensePanel";
import { ExpenseList } from "../components/ExpenseList";
import { MenuDrawer } from "../components/MenuDrawer";
import { MonthHeader } from "../components/MonthHeader";
import { SummaryRow } from "../components/SummaryRow";
import { useExpenses } from "../hooks/useExpenses";
import { useMonth } from "../hooks/useMonth";
import { clearTokens, getStoredTokens, refreshAccessToken } from "../services/auth";
import { updateExpense } from "../services/expenses";
import { getProfile, updateProfile } from "../services/profile";
import { Expense } from "../types/expense";
import { formatAmount } from "../utils/format";
import styles from "../styles/dashboard.module.css";

export default function Home() {
  const [editing, setEditing] = useState<Expense | null>(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const [profileName, setProfileName] = useState("");
  const lastListScroll = useRef<number | null>(null);
  const [editForm, setEditForm] = useState({
    amount: "",
    currency: "",
    category: "",
    merchant: "",
    notes: "",
    expense_date: "",
  });

  const onAuthFail = useCallback(() => {
    if (typeof window !== "undefined") {
      clearTokens();
      window.location.href = "/login";
    }
  }, []);

  const { expenses, setExpenses, loading, error, setError } = useExpenses(onAuthFail);
  const { monthLabel, groupedExpenses, filteredExpenses, shiftMonth } = useMonth(expenses);

  const summary = useMemo(() => {
    if (!filteredExpenses.length) {
      return {
        total: 0,
        currency: "",
        merchantCount: 0,
        categoryCount: 0,
      };
    }
    const total = filteredExpenses.reduce((sum, expense) => sum + expense.amount, 0);
    const currency = filteredExpenses[0]?.currency ?? "";
    const merchantCount = new Set(filteredExpenses.map((expense) => expense.merchant || "Unknown")).size;
    const categoryCount = new Set(filteredExpenses.map((expense) => expense.category || "Uncategorized")).size;
    return { total, currency, merchantCount, categoryCount };
  }, [filteredExpenses]);

  const startEdit = (expense: Expense) => {
    setEditing(expense);
    setEditForm({
      amount: expense.amount.toString(),
      currency: expense.currency || "USD",
      category: expense.category || "",
      merchant: expense.merchant || "",
      notes: expense.notes || "",
      expense_date: expense.expense_date ? expense.expense_date.slice(0, 10) : "",
    });
  };

  const cancelEdit = () => {
    setEditing(null);
  };

  const handleSaveEdit = async (event: FormEvent) => {
    event.preventDefault();
    if (!editing) return;
    try {
      const { accessToken } = getStoredTokens();
      if (!accessToken) {
        onAuthFail();
        return;
      }
      const payload = {
        amount: Number(editForm.amount),
        currency: editForm.currency,
        category: editForm.category || null,
        merchant: editForm.merchant || null,
        notes: editForm.notes || null,
        expense_date: editForm.expense_date,
      };
      const res = await updateExpense(editing.id, accessToken, payload);
      if (res.status === 401) {
        const refreshed = await refreshAccessToken();
        if (!refreshed) throw new Error("Unauthorized");
        const retry = await updateExpense(editing.id, refreshed, payload);
        if (!retry.ok) throw new Error("Failed to update expense");
        const updated = await retry.json();
        setExpenses((prev) => prev.map((item) => (item.id === editing.id ? updated : item)));
        setEditing(null);
        return;
      }
      if (!res.ok) throw new Error("Failed to update expense");
      const updated = await res.json();
      setExpenses((prev) => prev.map((item) => (item.id === editing.id ? updated : item)));
      setEditing(null);
    } catch (err) {
      console.error(err);
      setError("Failed to update expense");
    }
  };

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (editing) {
      if (lastListScroll.current === null) {
        lastListScroll.current = window.scrollY;
      }
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    if (lastListScroll.current !== null) {
      window.scrollTo({ top: lastListScroll.current, behavior: "auto" });
      lastListScroll.current = null;
    }
  }, [editing]);

  const handleLogout = () => {
    if (typeof window !== "undefined") {
      clearTokens();
      window.location.href = "/login";
    }
  };

  const handleSaveName = async (name: string) => {
    if (!name) return;
    const { accessToken } = getStoredTokens();
    if (!accessToken) return;
    const res = await updateProfile(accessToken, name);
    if (res.status === 401) {
      const refreshed = await refreshAccessToken();
      if (!refreshed) return;
      await updateProfile(refreshed, name);
    }
    setProfileName(name);
  };

  const loadProfile = async () => {
    const { accessToken } = getStoredTokens();
    if (!accessToken) return;
    const res = await getProfile(accessToken);
    if (res.status === 401) {
      const refreshed = await refreshAccessToken();
      if (!refreshed) return;
      const retry = await getProfile(refreshed);
      if (!retry.ok) return;
      const data = await retry.json();
      setProfileName(data.name || "");
      return;
    }
    if (!res.ok) return;
    const data = await res.json();
    setProfileName(data.name || "");
  };

  return (
    <main className={styles.page}>
      <div className={styles.shell}>
        <div
          className={styles.viewSwitcher}
          data-editing={editing ? "true" : "false"}
        >
          <div className={styles.view}>
            <MonthHeader
              monthLabel={monthLabel}
              onPrev={() => shiftMonth(-1)}
              onNext={() => shiftMonth(1)}
              onMenu={() => {
                setMenuOpen(true);
                loadProfile();
              }}
            />
            <SummaryRow
              totalLabel="Expenses"
              totalValue={summary.total ? formatAmount(summary.total, summary.currency) : "—"}
              merchantCount={summary.merchantCount}
              categoryCount={summary.categoryCount}
            />
            <ExpenseList
              groupedExpenses={groupedExpenses}
              fallbackCurrency={summary.currency}
              onEdit={startEdit}
              loading={loading}
              error={error}
            />
          </div>
          <div className={styles.view}>
            <EditExpensePanel
              editing={editing}
              form={editForm}
              onChange={setEditForm}
              onCancel={cancelEdit}
              onSubmit={handleSaveEdit}
            />
          </div>
        </div>
        <MenuDrawer
          isOpen={menuOpen}
          name={profileName}
          onClose={() => setMenuOpen(false)}
          onSaveName={handleSaveName}
          onLogout={handleLogout}
        />
      </div>
    </main>
  );
}
