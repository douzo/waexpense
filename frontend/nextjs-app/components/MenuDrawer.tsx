import { FormEvent, useEffect, useState } from "react";

import styles from "../styles/dashboard.module.css";

interface MenuDrawerProps {
  isOpen: boolean;
  name: string;
  onClose: () => void;
  onSaveName: (name: string) => Promise<void>;
  onLogout: () => void;
}

export const MenuDrawer = ({
  isOpen,
  name,
  onClose,
  onSaveName,
  onLogout,
}: MenuDrawerProps) => {
  const [draft, setDraft] = useState(name);

  useEffect(() => {
    if (isOpen) {
      setDraft(name);
    }
  }, [isOpen, name]);

  if (!isOpen) return null;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    await onSaveName(draft.trim());
  };

  return (
    <div
      className={styles.menuOverlay}
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <aside className={styles.menuDrawer} onClick={(event) => event.stopPropagation()}>
        <div className={styles.menuHeader}>
          <div>
            <p>Menu</p>
            <span>Profile & Settings</span>
          </div>
          <button className={styles.iconButton} onClick={onClose} aria-label="Close menu">
            ✕
          </button>
        </div>

        <div className={styles.menuSection}>
          <p>Profile</p>
          <form className={styles.menuForm} onSubmit={handleSubmit}>
            <label>
              Your name
              <input
                type="text"
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="Add your name"
              />
            </label>
            <button type="submit" className={styles.primaryBtn}>
              Save profile
            </button>
          </form>
        </div>

        <div className={styles.menuSection}>
          <p>Account</p>
          <div className={styles.menuActions}>
            <button className={styles.ghostBtn} onClick={onLogout}>
              Log out
            </button>
          </div>
        </div>
      </aside>
    </div>
  );
};
