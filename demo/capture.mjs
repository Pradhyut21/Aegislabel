/** Real app footage. Uses an isolated synthetic DB; never simulates result screens. */
import { chromium, expect } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";
const root = path.resolve(import.meta.dirname, "..");
const scenes = JSON.parse(
  fs.readFileSync(path.join(root, "artifacts/demo/scenes.json"), "utf8"),
);
const base = process.env.DEMO_BASE_URL || "http://127.0.0.1:8002";
const browser = await chromium.launch();
const context = await browser.newContext({
  baseURL: base,
  viewport: { width: 1600, height: 900 },
  recordVideo: {
    dir: path.join(root, "artifacts/demo/raw"),
    size: { width: 1600, height: 900 },
  },
  acceptDownloads: true,
});
await context.addInitScript(() => {
  document.addEventListener("DOMContentLoaded", () => {
    const pointer = document.createElement("div");
    pointer.setAttribute("aria-hidden", "true");
    pointer.style.cssText =
      "position:fixed;left:-50px;top:-50px;width:20px;height:20px;border:3px solid white;background:#0D9488;border-radius:50%;box-shadow:0 1px 5px #10263f88;pointer-events:none;z-index:999999";
    document.body.append(pointer);
    document.addEventListener("mousemove", (e) => {
      pointer.style.left = e.clientX - 10 + "px";
      pointer.style.top = e.clientY - 10 + "px";
    });
  });
});
const page = await context.newPage();
const epoch = Date.now();
const button = (name) => page.getByRole("button", { name, exact: true });
async function click(locator) {
  const element = locator.first();
  await element.scrollIntoViewIfNeeded();
  const box = await element.boundingBox();
  if (box)
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, {
      steps: 16,
    });
  await page.waitForTimeout(220);
  await element.click();
  await page.waitForTimeout(350);
}
async function dismiss() {
  const b = page.getByLabel("Dismiss notification");
  if (await b.isVisible()) await b.click();
}
async function stage(id, fn) {
  const scene = scenes.find((s) => s.id === id);
  const start = Date.now();
  await fn();
  await dismiss();
  const spent = Date.now() - start;
  await page.waitForTimeout(Math.max(400, scene.duration * 1000 - spent));
  scene.media_start = (start - epoch) / 1000;
  scene.duration = (Date.now() - start) / 1000;
  console.log(id, scene.media_start, scene.duration);
}
await page.goto("/");
await click(button("Sign in"));
await expect(
  page.getByRole("heading", { name: "Every change. Accounted for." }),
).toBeVisible();
await dismiss();
await stage("overview", async () => {
  await page.mouse.move(650, 460, { steps: 20 });
});
await stage("change", async () => {
  await click(button("New source change"));
  await page.getByLabel("Revised safety warning").fill("");
  await page
    .getByLabel("Revised safety warning")
    .pressSequentially("Do not reuse. Inspect packaging before use.", {
      delay: 32,
    });
  await click(button("Detect & assess impact"));
  await expect(
    page.getByText("2 affected labels", { exact: true }),
  ).toBeVisible();
  await page.mouse.move(1120, 500, { steps: 20 });
});
await stage("draft", async () => {
  await click(button("Generate draft"));
  await click(button("Edit artwork"));
  const warning = page
    .getByRole("dialog")
    .getByLabel("warning", { exact: true });
  await warning.fill("");
  await warning.pressSequentially("Do not reuse.", { delay: 55 });
  await click(button("Save new revision"));
});
await stage("blocked", async () => {
  await click(button("Run validation"));
  await expect(
    page.getByText("BLOCKED", { exact: true }).first(),
  ).toBeVisible();
  await expect(button("Submit for review")).toBeDisabled();
  const finding = page.locator(".finding-card");
  await finding.scrollIntoViewIfNeeded();
  const box = await finding.boundingBox();
  if (box) await page.mouse.move(box.x + 100, box.y + 100, { steps: 20 });
});
await stage("correct", async () => {
  await click(button("Regenerate from source"));
  await click(button("Run validation"));
  await expect(
    page.getByText("PASS FOR REVIEW", { exact: true }),
  ).toBeVisible();
  await page.waitForTimeout(1200);
  await click(button("Submit for review"));
  await click(button("Review & release"));
});
await stage("review", async () => {
  await click(page.getByLabel("Sign out"));
  await page.getByLabel("Username", { exact: true }).fill("reviewer");
  await page
    .getByLabel("Password", { exact: true })
    .fill("Aegis-reviewer-2026!");
  await click(button("Sign in"));
  await click(button("Review & release"));
  await click(button("Approve exact version"));
  await page.waitForTimeout(1600);
  await click(button("Confirm approval"));
});
await stage("release", async () => {
  await click(button("Generate release package"));
  const promise = page.waitForEvent("download");
  await click(
    page
      .getByRole("dialog")
      .getByRole("link", { name: "Download release ZIP" }),
  );
  const download = await promise;
  await download.saveAs(path.join(root, "artifacts/demo/release-package.zip"));
  await page.waitForTimeout(2200);
  await click(page.getByLabel("Close dialog"));
});
await stage("mutations", async () => {
  await click(button("Mutation Lab"));
  await click(button("Run regression suite"));
  await expect(page.getByText("24 / 24", { exact: true })).toBeVisible();
  await page.waitForTimeout(2300);
  await page.mouse.wheel(0, 390);
});
await stage("audit", async () => {
  await click(button("Evidence & audit"));
  await click(button("Verify chain integrity"));
  await expect(page.getByText(/Chain verified/)).toBeVisible();
  await page.waitForTimeout(1600);
  await click(
    page.locator(".audit-row").filter({ hasText: "RELEASE CREATED" }).first(),
  );
  await page.waitForTimeout(2000);
  await click(page.getByLabel("Close dialog"));
});
const video = page.video();
await context.close();
await video.saveAs(path.join(root, "demo/composition/assets/app-footage.webm"));
await browser.close();
fs.writeFileSync(
  path.join(root, "artifacts/demo/capture.json"),
  JSON.stringify(scenes, null, 2),
);
console.log("Actual app recording saved.");
