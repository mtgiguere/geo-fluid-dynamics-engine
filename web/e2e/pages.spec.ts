import { expect, test, type Page } from "@playwright/test";

// One smoke test per public static page, against the production build at
// the real deployment base path. Integration only (the Frontend Line): the
// numbers on these pages are tested in Python (geofluid.report and the
// golden tests) and in Vitest (calc.js, waves.js). What only a browser can
// prove is that each page loads where it is deployed, finds its data, runs
// its script and draws, with nothing failing along the way.

/** Every page error, console error and HTTP >= 400 response, with its URL. */
function collectErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => {
    if (m.type() === "error") errors.push(m.text());
  });
  page.on("response", (r) => {
    if (r.status() >= 400) errors.push(`HTTP ${r.status()} ${r.url()}`);
  });
  return errors;
}

test("demo: all 105 Kansas counties are drawn, console clean", async ({ page }) => {
  const errors = collectErrors(page);
  await page.goto("./demo.html");

  await expect(page.locator("path.county")).toHaveCount(105);
  expect(errors).toEqual([]);
});

test("forecast: 115 Missouri counties are drawn and the measure switcher recolours them", async ({
  page,
}) => {
  const errors = collectErrors(page);
  await page.goto("./forecast.html");

  // Missouri's 114 counties plus St. Louis city; Kansas City reports
  // separately in the predictions but has no polygon of its own.
  await expect(page.locator("path.county")).toHaveCount(115);
  // Adair is 0.489 on Amendment 3 and 0.347 on Amendment 8: switching
  // measure must change its colour, which proves the embedded data and the
  // page script are wired together.
  const adair = page.locator('path.county[data-fips="29001"]');
  const before = await adair.getAttribute("fill");
  await page.locator("#measure").selectOption("mo_20261103_amendment_8");
  await expect(adair).not.toHaveAttribute("fill", before ?? "");
  expect(errors).toEqual([]);
});

test("blueprint: all eight research figures decode, console clean", async ({ page }) => {
  const errors = collectErrors(page);
  await page.goto("./blueprint.html");

  const figures = page.locator("img");
  await expect(figures).toHaveCount(8);
  // Embedded as data URIs from the executed notebooks; a figure that fails
  // to decode has naturalWidth 0.
  const widths = await figures.evaluateAll((imgs) =>
    imgs.map((i) => (i as HTMLImageElement).naturalWidth),
  );
  expect(widths.filter((w) => w === 0)).toEqual([]);
  expect(errors).toEqual([]);
});

test("waves: the player fetches its data at the deploy path and draws every county", async ({
  page,
}) => {
  const errors = collectErrors(page);
  await page.goto("./waves.html");

  // data/waves.json is fetched at runtime by a relative URL: the exact kind
  // of path a wrong base path breaks (Bug #8). 3,108 counties and 7 topics
  // are what scripts/build_wave_player.py writes.
  await expect(page.locator("#map > path")).toHaveCount(3108, { timeout: 30_000 });
  await expect(page.locator("#topic option")).toHaveCount(7);
  expect(errors).toEqual([]);
});
