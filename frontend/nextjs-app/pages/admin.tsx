import { FormEvent, useState } from "react";

import styles from "../styles/admin.module.css";

export default function Admin() {
  const [adminToken, setAdminToken] = useState("");
  const [whatsappId, setWhatsappId] = useState("");
  const [isPremium, setIsPremium] = useState(false);
  const [status, setStatus] = useState<{ tone: "ok" | "error"; message: string } | null>(
    null
  );
  const [submitting, setSubmitting] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setStatus(null);
    setSubmitting(true);
    try {
      const res = await fetch(`${apiBase}/api/admin/users/${whatsappId}/premium`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          "X-Admin-Token": adminToken,
        },
        body: JSON.stringify({ is_premium: isPremium }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to update user");
      }
      setStatus({
        tone: "ok",
        message: `User ${whatsappId} set to ${isPremium ? "Premium" : "Free"}.`,
      });
    } catch (err: any) {
      setStatus({ tone: "error", message: err.message || "Request failed" });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className={styles.page}>
      <section className={styles.card}>
        <header className={styles.header}>
          <p className={styles.eyebrow}>Admin</p>
          <h1>Premium Control</h1>
          <p className={styles.subtitle}>
            Toggle premium access for a WhatsApp ID.
          </p>
        </header>

        {status && (
          <div className={`${styles.status} ${styles[status.tone]}`}>
            {status.message}
          </div>
        )}

        <form className={styles.form} onSubmit={handleSubmit}>
          <label>
            Admin token
            <input
              type="password"
              value={adminToken}
              onChange={(e) => setAdminToken(e.target.value)}
              placeholder="X-Admin-Token"
              required
            />
          </label>
          <label>
            WhatsApp ID
            <input
              type="text"
              value={whatsappId}
              onChange={(e) => setWhatsappId(e.target.value)}
              placeholder="15551234567"
              required
            />
          </label>
          <label className={styles.toggleRow}>
            <input
              type="checkbox"
              checked={isPremium}
              onChange={(e) => setIsPremium(e.target.checked)}
            />
            Set as Premium
          </label>
          <button type="submit" disabled={submitting}>
            {submitting ? "Updating…" : "Update user"}
          </button>
        </form>
      </section>
    </main>
  );
}
