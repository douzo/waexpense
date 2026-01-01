import { useCallback, useEffect, useState } from "react";

import { Expense } from "../types/expense";
import { clearTokens, getStoredTokens, refreshAccessToken } from "../services/auth";
import { fetchExpenses } from "../services/expenses";

export const useExpenses = (onAuthFail: () => void) => {
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        if (active) {
          setLoading(true);
          setError(null);
        }
        const { accessToken } = getStoredTokens();
        if (!accessToken) {
          onAuthFail();
          return;
        }
        const res = await fetchExpenses(accessToken);
        if (res.status === 401) {
          const refreshed = await refreshAccessToken();
          if (!refreshed) {
            clearTokens();
            onAuthFail();
            return;
          }
          const retry = await fetchExpenses(refreshed);
          if (!retry.ok) throw new Error("Failed to load expenses");
          const data = await retry.json();
          if (active) setExpenses(data.items);
          return;
        }
        if (!res.ok) throw new Error("Failed to load expenses");
        const data = await res.json();
        if (active) setExpenses(data.items);
      } catch (err) {
        console.error(err);
        if (active) setError("Failed to load expenses");
      } finally {
        if (active) setLoading(false);
      }
    };
    load();
    return () => {
      active = false;
    };
  }, [onAuthFail, reloadKey]);

  return { expenses, setExpenses, loading, error, setError, reload };
};
