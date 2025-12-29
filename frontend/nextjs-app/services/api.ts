const apiBase = process.env.NEXT_PUBLIC_API_BASE || "http://127.0.0.1:8000";

export const apiFetch = async (
  path: string,
  options: RequestInit = {}
): Promise<Response> => {
  return fetch(`${apiBase}${path}`, options);
};
