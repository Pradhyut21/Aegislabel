import { test, expect, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
async function signIn(page: Page, role = "author") {
  await page.goto("/");
  if (await page.getByLabel("Sign out").isVisible())
    await page.getByLabel("Sign out").click();
  await page.getByLabel("Username", { exact: true }).fill(role);
  await page
    .getByLabel("Password", { exact: true })
    .fill(`Aegis-${role}-2026!`);
  await page.getByRole("button", { name: "Sign in", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Every change. Accounted for." }),
  ).toBeVisible();
}
async function accessible(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"])
    .analyze();
  expect(
    results.violations.map((v) => ({
      id: v.id,
      nodes: v.nodes.map((n) => ({
        target: n.target,
        summary: n.failureSummary,
      })),
    })),
  ).toEqual([]);
}
test("real missed-warning failure, correction, reviewer approval and release download", async ({
  page,
}) => {
  await signIn(page);
  const session = await (await page.request.get("/api/v1/auth/me")).json();
  await page.request.post("/api/v1/changes", {
    headers: { "X-CSRF-Token": session.csrf },
    data: { device_id: "device-cardiac", warning: "Do not reuse." },
  });
  await page.reload();
  await page
    .getByRole("button", { name: "New source change", exact: true })
    .click();
  await page
    .getByLabel("Revised safety warning")
    .fill("Do not reuse. Inspect packaging before use.");
  await page.getByRole("button", { name: "Detect & assess impact" }).click();
  await expect(
    page.getByText("2 affected labels", { exact: true }).first(),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Generate draft", exact: true })
    .first()
    .click();
  await expect(
    page.getByRole("heading", { name: "Proposed artwork", exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Edit artwork", exact: true }).click();
  await page
    .getByRole("dialog")
    .getByLabel("warning", { exact: true })
    .fill("Do not reuse.");
  await page.getByRole("button", { name: "Save new revision" }).click();
  await page
    .getByRole("button", { name: "Run validation", exact: true })
    .first()
    .click();
  await expect(
    page.getByText("SAFETY WARNING MISMATCH", { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page.getByText("BLOCKED", { exact: true }).first(),
  ).toBeVisible();
  await accessible(page);
  await page.getByRole("button", { name: "Regenerate from source" }).click();
  await page
    .getByRole("button", { name: "Run validation", exact: true })
    .first()
    .click();
  await expect(
    page.getByText("PASS FOR REVIEW", { exact: true }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Submit for review", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Review & release", exact: true })
    .click();
  await expect(page.getByText("Sign in as reviewer to approve.")).toBeVisible();
  await signIn(page, "reviewer");
  await page
    .getByRole("button", { name: "Review & release", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Approve exact version" })
    .first()
    .click();
  await page
    .getByRole("button", { name: "Confirm approval", exact: true })
    .click();
  await page
    .getByRole("button", { name: "Generate release package" })
    .first()
    .click();
  const downloaded = page.waitForEvent("download");
  await page
    .getByRole("dialog")
    .getByRole("link", { name: "Download release ZIP" })
    .click();
  const file = await downloaded;
  expect(file.suggestedFilename()).toMatch(/aegis-release.*\.zip/);
  await page.getByLabel("Close dialog").click();
  await page
    .getByRole("button", { name: "Mutation Lab", exact: false })
    .click();
  await page
    .getByRole("button", { name: "Run regression suite", exact: true })
    .first()
    .click();
  await expect(page.getByText("24 / 24", { exact: true })).toBeVisible();
  await page
    .getByRole("button", { name: "Test latest change", exact: true })
    .click();
  await expect(page.getByText(/^change-targeted/)).toBeVisible();
  await expect(
    page.getByRole("row").filter({ hasText: "Wrong device identifier" }),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "Run regression suite", exact: true })
    .first()
    .click();
  await expect(page.getByText("24 / 24", { exact: true })).toBeVisible();

  await page
    .getByRole("button", { name: "Evidence & audit", exact: true })
    .click();
  await page.getByRole("button", { name: "Verify chain integrity" }).click();
  await expect(page.getByText(/Chain verified/)).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Every change. Accounted for." }),
  ).toBeVisible();
});
test("all main views are accessible and mobile navigation works without page overflow", async ({
  page,
}) => {
  await signIn(page);
  for (const name of [
    "Overview",
    "Device registry",
    "Document intelligence",
    "Change impact",
    "Label Studio",
    "Validation center",
    "Mutation Lab",
    "Review & release",
    "Evidence & audit",
    "Evaluation",
  ]) {
    await page
      .getByRole("button", { name, exact: name !== "Mutation Lab" })
      .first()
      .click();
    await accessible(page);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByLabel("Open navigation").click();
  await page.getByRole("button", { name: "Overview", exact: true }).click();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await accessible(page);
  await page
    .getByRole("button", { name: "New source change", exact: true })
    .click();
  await accessible(page);
  await page.keyboard.press("Escape");
  await expect(page.getByRole("dialog")).not.toBeVisible();
  await page.setViewportSize({ width: 320, height: 740 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await accessible(page);
  await page.screenshot({
    path: "../artifacts/mobile-verified.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.evaluate(() => {
    window.scrollTo(0, 0);
    (document.activeElement as HTMLElement)?.blur();
  });
  await page.screenshot({
    path: "../artifacts/overview-verified.png",
    fullPage: true,
  });
});
