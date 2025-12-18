import { useEffect, useMemo, useState } from "react";

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
  const [loading, setLoading] = useState(true);
  const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchExpenses() {
      try {
        const token =
          typeof window !== "undefined"
            ? localStorage.getItem("wa_token")
            : null;

        if (!token) {
          if (typeof window !== "undefined") {
            window.location.href = "/login";
          }
          return;
        }

        const res = await fetch(`${apiBase}/api/expenses`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (res.status === 401) {
          if (typeof window !== "undefined") {
            localStorage.removeItem("wa_token");
            window.location.href = "/login";
          }
          return;
        }
        if (!res.ok) throw new Error("Failed to load expenses");
        const data = await res.json();
        setExpenses(data.items);
      } catch (err) {
        console.error(err);
        setError("Failed to load expenses");
      } finally {
        setLoading(false);
      }
    }

    fetchExpenses();
  }, []);

  const summary = useMemo(() => {
    if (!expenses.length) {
      return {
        total: 0,
        currency: "",
        merchantCount: 0,
        categoryCount: 0,
      };
    }
    const total = expenses.reduce((sum, expense) => sum + expense.amount, 0);
    const currency = expenses[0]?.currency ?? "";
    const merchantCount = new Set(expenses.map((expense) => expense.merchant || "Unknown")).size;
    const categoryCount = new Set(expenses.map((expense) => expense.category || "Uncategorized")).size;
    return { total, currency, merchantCount, categoryCount };
  }, [expenses]);

  const formatDate = (value: string) => {
    const date = value ? new Date(value) : null;
    if (!date || Number.isNaN(date.getTime())) return "—";
    return date.toLocaleDateString(undefined, {
      day: "numeric",
      month: "short",
      year: "numeric",
    });
  };

  const formatAmount = (amount: number, currency: string) => {
    try {
      return new Intl.NumberFormat(undefined, {
        style: "currency",
        currency: currency || "USD",
        maximumFractionDigits: 2,
      }).format(amount);
    } catch {
      return `${amount.toFixed(2)} ${currency}`;
    }
  };

  const handleLogout = () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("wa_token");
      window.location.href = "/login";
    }
  };

  return (
    <main className="page">
      <div className="shell">
        <header className="hero">
          <div>
            <p className="eyebrow">Dashboard</p>
            <h1>WhatsApp Expense Tracker</h1>
            <p className="subtitle">
              Track spending submitted via WhatsApp in a clean, minimal overview.
            </p>
          </div>
          <button className="ghost-btn" onClick={handleLogout}>
            Log out
          </button>
        </header>

        <section className="summary-grid">
          <article className="summary-card">
            <p>Total spent</p>
            <strong>
              {summary.total
                ? formatAmount(summary.total, summary.currency)
                : "—"}
            </strong>
          </article>
          <article className="summary-card">
            <p>Active merchants</p>
            <strong>{summary.merchantCount}</strong>
          </article>
          <article className="summary-card">
            <p>Categories</p>
            <strong>{summary.categoryCount}</strong>
          </article>
        </section>

        <section className="table-card">
          <div className="table-header">
            <p>Recent expenses</p>
            <span className="badge">{expenses.length}</span>
          </div>

          {error && <p className="error">{error}</p>}
          {loading ? (
            <div className="empty">Loading your expenses…</div>
          ) : expenses.length === 0 ? (
            <div className="empty">
              Nothing to show yet. Send a receipt via WhatsApp to see it here.
            </div>
          ) : (
            <div className="table-wrapper">
              <table>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Merchant</th>
                    <th>Category</th>
                    <th className="right">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {expenses.map((expense) => (
                    <tr key={expense.id}>
                      <td>{formatDate(expense.expense_date)}</td>
                      <td>{expense.merchant || "—"}</td>
                      <td>{expense.category || "Uncategorized"}</td>
                      <td className="right">
                        {formatAmount(expense.amount, expense.currency)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      <style jsx>{`
        :global(body) {
          margin: 0;
          background: #0f172a;
          font-family: "Inter", ui-sans-serif, system-ui, -apple-system,
            BlinkMacSystemFont, "Segoe UI", sans-serif;
          color: #0f172a;
        }

        .page {
          min-height: 100vh;
          background: radial-gradient(circle at 0% 0%, #1d4ed8, #0f172a 45%),
            #0f172a;
          display: flex;
          justify-content: center;
          padding: 3rem 1.5rem;
        }

        .shell {
          width: min(1100px, 100%);
          background: #f8fafc;
          border-radius: 28px;
          padding: 3rem;
          box-shadow: 0 20px 60px rgba(15, 23, 42, 0.35);
        }

        .hero {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 1rem;
        }

        .eyebrow {
          text-transform: uppercase;
          letter-spacing: 0.16em;
          font-size: 0.75rem;
          color: #2563eb;
          margin: 0 0 0.25rem;
        }

        h1 {
          margin: 0;
          font-size: clamp(2rem, 3vw, 3rem);
        }

        .subtitle {
          margin: 0.6rem 0 0;
          color: #475569;
        }

        .ghost-btn {
          border: 1px solid rgba(15, 23, 42, 0.12);
          background: transparent;
          color: #0f172a;
          padding: 0.65rem 1.25rem;
          border-radius: 999px;
          cursor: pointer;
          font-weight: 600;
          transition: border-color 0.2s ease, color 0.2s ease;
        }

        .ghost-btn:hover {
          border-color: #0f172a;
          color: #1d4ed8;
        }

        .summary-grid {
          margin-top: 2.5rem;
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
          gap: 1rem;
        }

        .summary-card {
          background: white;
          border-radius: 18px;
          padding: 1.5rem;
          box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.05);
        }

        .summary-card p {
          margin: 0;
          color: #94a3b8;
          font-size: 0.9rem;
        }

        .summary-card strong {
          display: block;
          margin-top: 0.5rem;
          font-size: 1.75rem;
          color: #0f172a;
        }

        .table-card {
          margin-top: 2.5rem;
          background: white;
          border-radius: 22px;
          padding: 2rem;
          box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.04);
        }

        .table-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 1rem;
          color: #0f172a;
          font-weight: 600;
        }

        .badge {
          background: #e0e7ff;
          color: #312e81;
          padding: 0.2rem 0.65rem;
          border-radius: 999px;
          font-size: 0.85rem;
        }

        .error {
          color: #dc2626;
          margin-bottom: 0.75rem;
        }

        .empty {
          text-align: center;
          color: #64748b;
          padding: 2.5rem 0;
        }

        .table-wrapper {
          overflow-x: auto;
        }

        table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.95rem;
        }

        th {
          text-align: left;
          color: #94a3b8;
          font-weight: 500;
          padding-bottom: 0.75rem;
        }

        td {
          padding: 0.9rem 0;
          border-top: 1px solid rgba(148, 163, 184, 0.2);
        }

        td.right,
        th.right {
          text-align: right;
        }

        tr:last-child td {
          border-bottom: none;
        }

        @media (max-width: 768px) {
          .shell {
            padding: 2rem;
          }

          .hero {
            flex-direction: column;
          }

          th:nth-child(3),
          td:nth-child(3) {
            display: none;
          }
        }
      `}</style>
    </main>
  );
}
