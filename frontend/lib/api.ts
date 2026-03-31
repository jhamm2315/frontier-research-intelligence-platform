export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export function buildApiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

export async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(buildApiUrl(path), {
    cache: "no-store",
    ...init,
  });

  if (!res.ok) {
    throw new Error(`API request failed: ${res.status}`);
  }

  return res.json();
}

export async function postApi<T>(
  path: string,
  body: unknown,
  init?: RequestInit,
): Promise<T> {
  return fetchApi<T>(path, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    body: JSON.stringify(body),
    ...init,
  });
}
