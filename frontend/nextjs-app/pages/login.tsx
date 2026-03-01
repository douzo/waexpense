import { FormEvent, useEffect, useMemo, useState } from "react";

type Step = "enter-wa" | "enter-code";
type StatusTone = "info" | "error" | "success";

export default function Login() {
  const [waId, setWaId] = useState("");
  const [step, setStep] = useState<Step>("enter-wa");
  const [code, setCode] = useState("");
  const [status, setStatus] = useState<{ message: string; tone: StatusTone } | null>(
    null
  );
  const [submitting, setSubmitting] = useState(false);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

  const steps = useMemo(
    () => [
      {
        id: "enter-wa" as Step,
        label: "Identify yourself",
        description: "Enter the WhatsApp ID you used with the bot.",
      },
      {
        id: "enter-code" as Step,
        label: "Verify code",
        description: "Enter the 6-digit code sent to your WhatsApp.",
      },
    ],
    []
  );

  useEffect(() => {
    if (typeof window !== "undefined") {
      // Basic diagnostic to confirm what API base the login page is using.
      console.info("[login] Page mounted", { apiBase });
    }
  }, [apiBase]);

  async function handleRequestCode(e: FormEvent) {
    e.preventDefault();
    setStatus(null);
    setSubmitting(true);
    try {
      console.info("[login] Requesting login code", {
        apiBase,
        whatsapp_id: waId,
      });
      const res = await fetch(`${apiBase}/auth/request-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ whatsapp_id: waId }),
      });
      console.info("[login] Request code response", {
        ok: res.ok,
        status: res.status,
        statusText: res.statusText,
        url: res.url,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
          console.error("[login] Request code failed", {
            status: res.status,
            statusText: res.statusText,
            detail: (data as any)?.detail,
          });
        throw new Error(data.detail || "Failed to request code");
      }
      setStatus({
        tone: "success",
        message: "Code sent to your WhatsApp. Please check your messages.",
      });
      console.info("[login] Login code requested successfully; moving to verify step");
      setStep("enter-code");
    } catch (err: any) {
      console.error("[login] Request code threw", err);
      setStatus({ tone: "error", message: err.message || "Something went wrong" });
    } finally {
      setSubmitting(false);
    }
  }

  async function handleVerifyCode(e: FormEvent) {
    e.preventDefault();
    setStatus(null);
    setSubmitting(true);
    try {
      console.info("[login] Verifying login code", {
        apiBase,
        whatsapp_id: waId,
        codeLength: code?.length ?? 0,
      });
      const res = await fetch(`${apiBase}/auth/verify-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ whatsapp_id: waId, code }),
      });
      console.info("[login] Verify code response", {
        ok: res.ok,
        status: res.status,
        statusText: res.statusText,
        url: res.url,
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        console.error("[login] Verify code failed", {
          status: res.status,
          statusText: res.statusText,
          detail: (data as any)?.detail,
        });
        throw new Error(data.detail || "Invalid code");
      }
      const data = await res.json();
      if (typeof window !== "undefined") {
        localStorage.setItem("wa_token", data.access_token);
        localStorage.setItem("wa_refresh_token", data.refresh_token);
        console.info("[login] Verify successful; tokens stored, redirecting to '/'");
        window.location.href = "/";
      }
    } catch (err: any) {
      console.error("[login] Verify code threw", err);
      setStatus({ tone: "error", message: err.message || "Something went wrong" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page">
      <div className="shell login">
        <div className="brand">
          <div className="brand-mark">W</div>
          <div className="brand-text">
            <span className="brand-name">WaExpense</span>
            <span className="brand-tagline">WhatsApp expense insights</span>
          </div>
        </div>

        <header className="hero">
          <div>
            <p className="eyebrow">Sign in</p>
            <h1>Access your WhatsApp expenses</h1>
            <p className="subtitle">
              We use a quick, secure WhatsApp verification—no password needed.
            </p>
          </div>
        </header>

        <section className="card">
          <ol className="stepper">
            {steps.map((item, idx) => {
              const isActive = step === item.id;
              const isCompleted =
                steps.findIndex((s) => s.id === step) > idx;
              return (
                <li
                  key={item.id}
                  className={[
                    "step",
                    isActive ? "active" : "",
                    isCompleted ? "completed" : "",
                  ]
                    .join(" ")
                    .trim()}
                >
                  <span className="step-index">{idx + 1}</span>
                  <div>
                    <p>{item.label}</p>
                    <small>{item.description}</small>
                  </div>
                </li>
              );
            })}
          </ol>

          {status && (
            <div className={`status ${status.tone}`}>
              {status.message}
            </div>
          )}

          {step === "enter-wa" ? (
            <form onSubmit={handleRequestCode} className="form">
              <label>
                WhatsApp ID / phone number
                <input
                  type="text"
                  value={waId}
                  onChange={(e) => setWaId(e.target.value)}
                  placeholder="e.g. 15551234567"
                  required
                />
              </label>
              <button type="submit" disabled={submitting}>
                {submitting ? "Sending code…" : "Send login code"}
              </button>
            </form>
          ) : (
            <form onSubmit={handleVerifyCode} className="form">
              <label>
                Verification code
                <input
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="6-digit code"
                  inputMode="numeric"
                  maxLength={6}
                  required
                />
              </label>
              <div className="actions">
                <button
                  type="button"
                  className="ghost-btn"
                  onClick={() => setStep("enter-wa")}
                >
                  Change WhatsApp ID
                </button>
                <button type="submit" disabled={submitting}>
                  {submitting ? "Verifying…" : "Verify & continue"}
                </button>
              </div>
            </form>
          )}

          <p className="trust-copy">
            Your WhatsApp number is only used for login. No passwords to remember,
            and you can revoke access anytime.
          </p>
        </section>

        <footer className="shell-footer" aria-label="Legal and help links">
          <span className="footer-copy">© {new Date().getFullYear()} WaExpense</span>
          <nav className="footer-links">
            <a href="#" className="footer-link">
              Privacy
            </a>
            <a href="#" className="footer-link">
              Terms
            </a>
            <a href="#" className="footer-link">
              Help
            </a>
          </nav>
        </footer>
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
          align-items: center;
          padding: 3rem 1.5rem;
        }

        .shell.login {
          width: min(520px, 100%);
          background: #f8fafc;
          border-radius: 28px;
          padding: 2.5rem;
          box-shadow: 0 20px 60px rgba(15, 23, 42, 0.35);
        }

        .brand {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          margin-bottom: 1.5rem;
        }

        .brand-mark {
          width: 32px;
          height: 32px;
          border-radius: 999px;
          background: radial-gradient(circle at 30% 20%, #ffffff, #1d4ed8);
          color: #eff6ff;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 700;
          font-size: 0.9rem;
          box-shadow: 0 6px 18px rgba(15, 23, 42, 0.35);
        }

        .brand-text {
          display: flex;
          flex-direction: column;
          gap: 0.1rem;
        }

        .brand-name {
          font-weight: 600;
          font-size: 0.95rem;
          letter-spacing: 0.02em;
          color: #0f172a;
        }

        .brand-tagline {
          font-size: 0.8rem;
          color: #64748b;
        }

        .hero {
          margin-bottom: 1.25rem;
        }

        .eyebrow {
          text-transform: uppercase;
          letter-spacing: 0.16em;
          font-size: 0.75rem;
          color: #2563eb;
          opacity: 0.9;
          margin: 0 0 0.4rem;
        }

        h1 {
          margin: 0;
          font-size: clamp(1.75rem, 3vw, 2.4rem);
        }

        .subtitle {
          margin-top: 0.75rem;
          color: #475569;
          max-width: 42ch;
        }

        .card {
          background: white;
          border-radius: 20px;
          padding: 1.75rem;
          box-shadow: inset 0 0 0 1px rgba(15, 23, 42, 0.04);
        }

        .stepper {
          list-style: none;
          padding: 0;
          margin: 0 0 1.5rem;
        }

        .step {
          display: flex;
          gap: 0.9rem;
          padding: 0.6rem 0.25rem;
          border-bottom: 1px solid rgba(148, 163, 184, 0.2);
        }

        .step:last-child {
          border-bottom: none;
        }

        .step.active {
          background: rgba(37, 99, 235, 0.06);
          border-radius: 12px;
        }

        .step-index {
          width: 32px;
          height: 32px;
          border-radius: 50%;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          font-weight: 600;
          color: #1d4ed8;
          background: rgba(29, 78, 216, 0.12);
        }

        .step.active .step-index {
          background: #1d4ed8;
          color: white;
        }

        .step.completed .step-index {
          background: #22c55e;
          color: white;
        }

        .step p {
          margin: 0;
          font-weight: 600;
        }

        .step.active p {
          font-size: 0.98rem;
        }

        .step small {
          display: block;
          margin-top: 0.2rem;
          color: #94a3b8;
        }

        .status {
          border-radius: 16px;
          padding: 0.85rem 1.2rem;
          font-size: 0.95rem;
          margin: 0.75rem 0 1rem;
          display: flex;
          align-items: flex-start;
          gap: 0.5rem;
          line-height: 1.4;
        }

        .status::before {
          content: "";
          width: 10px;
          height: 10px;
          border-radius: 999px;
          margin-top: 0.3rem;
        }

        .status.info {
          background: #e0f2fe;
          color: #0369a1;
          border: 1px solid rgba(56, 189, 248, 0.5);
        }

        .status.info::before {
          background: #0ea5e9;
        }

        .status.error {
          background: #fee2e2;
          color: #b91c1c;
          border: 1px solid rgba(248, 113, 113, 0.6);
        }

        .status.error::before {
          background: #ef4444;
        }

        .status.success {
          background: #dcfce7;
          color: #166534;
          border: 1px solid rgba(74, 222, 128, 0.7);
        }

        .status.success::before {
          background: #22c55e;
        }

        .form {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        label {
          font-weight: 600;
          color: #0f172a;
          display: flex;
          flex-direction: column;
          gap: 0.35rem;
        }

        input {
          border-radius: 12px;
          border: 1px solid rgba(15, 23, 42, 0.15);
          padding: 0.85rem 1rem;
          font-size: 1rem;
          background: #f8fafc;
        }

        input:focus {
          outline: 2px solid rgba(37, 99, 235, 0.35);
          outline-offset: 2px;
          border-color: rgba(37, 99, 235, 0.6);
          box-shadow: 0 0 0 1px rgba(191, 219, 254, 0.9);
        }

        button {
          border: none;
          border-radius: 999px;
          padding: 0.85rem 1.5rem;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          background: #1d4ed8;
          color: white;
          transition: opacity 0.2s ease, transform 0.1s ease, box-shadow 0.1s ease;
          box-shadow: 0 10px 25px rgba(37, 99, 235, 0.25);
        }

        button:hover:not(:disabled) {
          opacity: 0.95;
          transform: translateY(-1px);
          box-shadow: 0 14px 32px rgba(37, 99, 235, 0.35);
        }

        button:active:not(:disabled) {
          opacity: 0.9;
          transform: translateY(0);
          box-shadow: 0 8px 20px rgba(37, 99, 235, 0.25);
        }

        button:disabled {
          opacity: 0.65;
          cursor: not-allowed;
        }

        .ghost-btn {
          border: 1px solid rgba(15, 23, 42, 0.12);
          background: transparent;
          color: #0f172a;
        }

        .ghost-btn:hover:not(:disabled) {
          border-color: #1d4ed8;
          color: #1d4ed8;
          background: rgba(191, 219, 254, 0.35);
        }

        .actions {
          display: flex;
          gap: 0.75rem;
          flex-wrap: wrap;
        }

        .actions button {
          flex: 1 1 auto;
        }

        .trust-copy {
          margin-top: 1.25rem;
          font-size: 0.8rem;
          color: #94a3b8;
          line-height: 1.5;
        }

        .shell-footer {
          margin-top: 1.75rem;
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 0.75rem;
          font-size: 0.75rem;
          color: #64748b;
        }

        .footer-links {
          display: flex;
          gap: 0.9rem;
          flex-wrap: wrap;
        }

        .footer-link {
          color: inherit;
          text-decoration: none;
        }

        .footer-link:hover {
          text-decoration: underline;
        }

        @media (max-width: 640px) {
          .shell.login {
            padding: 1.75rem 1.25rem;
          }

          .card {
            padding: 1.2rem;
          }

          .brand {
            margin-bottom: 1.25rem;
          }

          .shell-footer {
            flex-direction: column;
            align-items: flex-start;
          }

          .actions {
            flex-direction: column;
          }

          .actions button {
            width: 100%;
          }
        }
      `}</style>
    </main>
  );
}
