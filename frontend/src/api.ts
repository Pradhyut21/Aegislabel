let csrf = "";
export const setCsrf = (v: string) => {
  csrf = v;
};
export async function api<T = unknown>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  const form = body instanceof FormData;
  const r = await fetch("/api/v1" + path, {
    method,
    credentials: "same-origin",
    headers: {
      ...(form ? {} : { "Content-Type": "application/json" }),
      "X-CSRF-Token": csrf,
    },
    body: body === undefined ? undefined : form ? body : JSON.stringify(body),
  });
  if (!r.ok) {
    let message = "Request failed";
    try {
      const e = await r.json();
      message =
        typeof e.detail === "string" ? e.detail : JSON.stringify(e.detail);
    } catch {
      message = await r.text().catch(() => message);
    }
    throw new Error(message);
  }
  return r.json();
}
