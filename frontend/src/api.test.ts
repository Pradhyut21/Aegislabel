import { describe, it, expect, vi, afterEach } from "vitest";
import { api, setCsrf } from "./api";
afterEach(() => vi.unstubAllGlobals());
describe("API transport", () => {
  it("sends server session CSRF token and serialized controlled edits", async () => {
    setCsrf("session-csrf");
    const fetcher = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ id: "revision" }), { status: 200 }),
      );
    vi.stubGlobal("fetch", fetcher);
    expect(await api("/drafts", "POST", { label_id: "label" })).toEqual({
      id: "revision",
    });
    expect(fetcher).toHaveBeenCalledWith(
      "/api/v1/drafts",
      expect.objectContaining({
        credentials: "same-origin",
        headers: expect.objectContaining({ "X-CSRF-Token": "session-csrf" }),
        body: JSON.stringify({ label_id: "label" }),
      }),
    );
  });
  it("surfaces safe server rejection instead of a success notice", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValue(
          new Response(
            JSON.stringify({ detail: "Independent reviewer required" }),
            { status: 403 },
          ),
        ),
    );
    await expect(api("/review", "POST", {})).rejects.toThrow(
      "Independent reviewer required",
    );
  });
  it("does not overwrite multipart boundaries on document uploads", async () => {
    const fetcher = vi.fn().mockResolvedValue(new Response("{}"));
    vi.stubGlobal("fetch", fetcher);
    const form = new FormData();
    form.set("file", new Blob(["pdf"]), "spec.pdf");
    await api("/documents/upload", "POST", form);
    expect(fetcher.mock.calls[0][1].headers).not.toHaveProperty("Content-Type");
  });
});
