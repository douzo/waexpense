import { apiFetch } from "./api";

export interface Profile {
  id: string;
  whatsapp_id: string;
  name?: string | null;
  default_currency?: string | null;
  is_premium: boolean;
}

export const getProfile = async (accessToken: string): Promise<Response> => {
  return apiFetch("/api/profile", {
    headers: {
      Authorization: `Bearer ${accessToken}`,
    },
  });
};

export const updateProfile = async (
  accessToken: string,
  name: string
): Promise<Response> => {
  return apiFetch("/api/profile", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify({ name }),
  });
};
