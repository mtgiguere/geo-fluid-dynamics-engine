import { expect, test } from "@playwright/test";

// Golden-path E2E: the production build, served at the real deployment
// sub-path, in a real browser, mocking nothing. Each test covers the most
// important thing a user does. If these pass, the deployed app works; if
// the base path, the data files, the token wiring, or the render pipeline
// break, they fail here — before any human opens the URL.

test.beforeEach(async ({ page }) => {
  // Stub Mapbox telemetry. events.mapbox.com 403s from CI runners (and the
  // GL library then logs minified errors), flooding the console with noise
  // that has nothing to do with OUR app's health. Fulfilling with 204 keeps
  // the clean-console assertion strict about everything that matters while
  // removing a third-party analytics endpoint from the deploy gate.
  await page.route(/events\.mapbox\.com/, (route) => route.fulfill({ status: 204, body: "" }));
});

test("map renders every county at the deployed base path, console clean", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  // Console "Failed to load resource" messages omit the URL, which cost two
  // blind debugging rounds (the real culprit was a Mapbox token missing the
  // TILES:READ scope — 403 on api.mapbox.com/v4 only). Capture every >=400
  // response WITH its URL so the assertion diff names the failing resource.
  page.on("response", (r) => {
    if (r.status() >= 400) errors.push(`HTTP ${r.status()} ${r.url()}`);
  });

  await page.goto("./");

  // 3,112 is the master panel's county count — a number, not a vibe.
  await expect(page.locator("#status")).toContainText("counties", { timeout: 30_000 });
  await expect(page.locator("#status")).toContainText("3,112");
  await expect(page.locator("#map canvas")).toBeVisible();
  expect(errors).toEqual([]);
});

test("clicking a county opens its data popup", async ({ page }) => {
  await page.goto("./");
  await expect(page.locator("#status")).toContainText("counties", { timeout: 30_000 });
  await page.waitForTimeout(3_000); // let tiles paint before clicking

  // Viewport center at this map center/zoom lands in the central plains —
  // any county works; the assertion is on the popup contract, not the county.
  await page.mouse.click(640, 400);

  const popup = page.locator(".mapboxgl-popup");
  await expect(popup).toBeVisible({ timeout: 15_000 });
  await expect(popup).toContainText("Two-party result");
  await expect(popup).toContainText("Bachelor's or higher");
});

test("metric switcher recolors the map and relabels the legend", async ({ page }) => {
  await page.goto("./");
  await expect(page.locator("#status")).toContainText("counties", { timeout: 30_000 });

  await page.locator("#metric").selectOption("swing_dem_2p");
  await expect(page.locator("#legend-left")).toHaveText("Swung Republican");

  await page.locator("#metric").selectOption("median_hh_income");
  await expect(page.locator("#legend-left")).toHaveText("$40k");
  await expect(page.locator("#legend-right")).toHaveText("$120k+");

  // The categorical wave-anchors layer: labeled chips plus the
  // plain-language caption (the Chicago-misreading lesson).
  await page.locator("#metric").selectOption("swing_lisa_quadrant");
  await expect(page.locator("#legend")).toContainText("Swung R together");
  await expect(page.locator("#legend")).toContainText("not partisan lean");
});

test("year slider scrubs to another election", async ({ page }) => {
  await page.goto("./");
  await expect(page.locator("#status")).toContainText("counties", { timeout: 30_000 });

  await page.locator("#year").fill("0");

  await expect(page.locator("#year-label")).toHaveText("2000");
  await expect(page.locator("#status")).toContainText("2000", { timeout: 15_000 });
});
