import { Expense } from "../types/expense";
import { apiFetch } from "./api";

export const fetchExpenses = async (accessToken: string) => {
  return apiFetch("/api/expenses", {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
};

export const updateExpense = async (
  expenseId: string,
  accessToken: string,
  payload: Partial<Expense> & { amount: number; expense_date: string }
) => {
  return apiFetch(`/api/expenses/${expenseId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  });
};
