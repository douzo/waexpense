import { useEffect, useState } from "react";

interface Expense {
  id: string;
  merchant: string;
  amount: number;
  currency: string;
  category: string;
  expense_date: string;
}

export default function Home() {
  const [expenses, setExpenses] = useState<Expense[]>([]);

  useEffect(() => {
    async function fetchExpenses() {
      try {
        const res = await fetch("/api/expenses");
        if (!res.ok) throw new Error("Failed to load expenses");
        const data = await res.json();
        setExpenses(data.items);
      } catch (err) {
        console.error(err);
      }
    }

    fetchExpenses();
  }, []);

  return (
    <main style={{ padding: "2rem", fontFamily: "Inter, sans-serif" }}>
      <h1>WhatsApp Expense Tracker</h1>
      <p>Recent expenses (dummy data)</p>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left" }}>Date</th>
            <th style={{ textAlign: "left" }}>Merchant</th>
            <th style={{ textAlign: "left" }}>Category</th>
            <th style={{ textAlign: "right" }}>Amount</th>
          </tr>
        </thead>
        <tbody>
          {expenses.map((expense) => (
            <tr key={expense.id} style={{ borderBottom: "1px solid #eee" }}>
              <td>{expense.expense_date}</td>
              <td>{expense.merchant}</td>
              <td>{expense.category}</td>
              <td style={{ textAlign: "right" }}>
                {expense.amount} {expense.currency}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
