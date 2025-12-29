import { apiFetch } from "./api";

export const getStoredTokens = () => {
  if (typeof window === "undefined") {
    return { accessToken: null, refreshToken: null };
  }
  return {
    accessToken: localStorage.getItem("wa_token"),
    refreshToken: localStorage.getItem("wa_refresh_token"),
  };
};

export const storeTokens = (accessToken: string, refreshToken: string) => {
  if (typeof window === "undefined") return;
  localStorage.setItem("wa_token", accessToken);
  localStorage.setItem("wa_refresh_token", refreshToken);
};

export const clearTokens = () => {
  if (typeof window === "undefined") return;
  localStorage.removeItem("wa_token");
  localStorage.removeItem("wa_refresh_token");
};

export const refreshAccessToken = async (): Promise<string | null> => {
  const { refreshToken } = getStoredTokens();
  if (!refreshToken) return null;
  const res = await apiFetch("/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  if (!res.ok) return null;
  const data = await res.json();
  storeTokens(data.access_token, data.refresh_token);
  return data.access_token;
};
