import { useMemo, useState } from "react";

import { Expense } from "../types/expense";

export const useMonth = (expenses: Expense[]) => {
  const [currentMonth, setCurrentMonth] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });

  const monthLabel = currentMonth.toLocaleDateString(undefined, {
    month: "short",
    year: "numeric",
  });

  const filteredExpenses = useMemo(() => {
    const month = currentMonth.getMonth();
    const year = currentMonth.getFullYear();
    return expenses.filter((expense) => {
      if (!expense.expense_date) return false;
      const date = new Date(expense.expense_date);
      return date.getMonth() === month && date.getFullYear() === year;
    });
  }, [currentMonth, expenses]);

  const groupedExpenses = useMemo(() => {
    const groups = new Map<string, Expense[]>();
    filteredExpenses.forEach((expense) => {
      const key = expense.expense_date ? expense.expense_date.slice(0, 10) : "Unknown";
      if (!groups.has(key)) groups.set(key, []);
      groups.get(key)!.push(expense);
    });
    return Array.from(groups.entries()).sort((a, b) => (a[0] < b[0] ? 1 : -1));
  }, [filteredExpenses]);

  const shiftMonth = (direction: -1 | 1) => {
    setCurrentMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() + direction, 1));
  };

  return { currentMonth, monthLabel, filteredExpenses, groupedExpenses, shiftMonth };
};
