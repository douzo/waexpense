import { FormEvent, useMemo, useState } from "react";

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

  async function handleRequestCode(e: FormEvent) {
    e.preventDefault();
    setStatus(null);
    setSubmitting(true);
    try {
      const res = await fetch(`${apiBase}/auth/request-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ whatsapp_id: waId }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to request code");
      }
      setStatus({
        tone: "success",
        message: "Code sent to your WhatsApp. Please check your messages.",
      });
      setStep("enter-code");
    } catch (err: any) {
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
      const res = await fetch(`${apiBase}/auth/verify-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ whatsapp_id: waId, code }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Invalid code");
      }
      const data = await res.json();
      if (typeof window !== "undefined") {
        localStorage.setItem("wa_token", data.access_token);
        window.location.href = "/";
      }
    } catch (err: any) {
      setStatus({ tone: "error", message: err.message || "Something went wrong" });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="page">
      <div className="shell login">
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

        .hero {
          margin-bottom: 1.5rem;
        }

        .eyebrow {
          text-transform: uppercase;
          letter-spacing: 0.16em;
          font-size: 0.75rem;
          color: #2563eb;
          margin: 0 0 0.4rem;
        }

        h1 {
          margin: 0;
          font-size: clamp(1.75rem, 3vw, 2.4rem);
        }

        .subtitle {
          margin-top: 0.75rem;
          color: #475569;
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
          padding: 0.75rem 0;
          border-bottom: 1px solid rgba(148, 163, 184, 0.2);
        }

        .step:last-child {
          border-bottom: none;
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

        .step small {
          display: block;
          margin-top: 0.2rem;
          color: #94a3b8;
        }

        .status {
          border-radius: 16px;
          padding: 0.85rem 1.2rem;
          font-size: 0.95rem;
          margin-bottom: 1rem;
        }

        .status.info {
          background: #e0f2fe;
          color: #0369a1;
        }

        .status.error {
          background: #fee2e2;
          color: #b91c1c;
        }

        .status.success {
          background: #dcfce7;
          color: #166534;
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
          transition: opacity 0.2s ease;
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
        }

        .actions {
          display: flex;
          gap: 0.75rem;
          flex-wrap: wrap;
        }

        @media (max-width: 640px) {
          .shell.login {
            padding: 2rem 1.5rem;
          }

          .card {
            padding: 1.25rem;
          }
        }
      `}</style>
    </main>
  );
}

