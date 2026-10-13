#!/usr/bin/env node
/**
 * Fetch county-level ballot-measure results from the Missouri Secretary of
 * State's Election Night Results portal (enr.sos.mo.gov) as page text files
 * that `geofluid.ingest.referendum.parse_mo_enr_results` can read.
 *
 * Why this exists: the SoS certifies results weeks before it posts the
 * canvass PDF (the Aug 4 2026 primary was certified 2026-08-25 and the PDF
 * was still absent in late September), but the portal serves the same
 * certified county numbers immediately. This is the election-night path for
 * November 2026 and the cross-check path when a canvass finally posts.
 *
 * Why a real Chrome: Cloudflare blocks plain curl and headless Chromium on
 * the portal's sub-pages. The installed Chrome channel with the automation
 * flag disabled gets through (verified 2026-09-14). Pages are navigated the
 * way a person would: front page -> "Pick a Race" link -> select a race ->
 * click Submit -> read the County / YES / NO table.
 *
 * Usage (from the repo root; Playwright is installed in web/):
 *   NODE_PATH=web/node_modules node scripts/fetch_mo_enr.cjs \
 *       --out data/raw --prefix enr_mo_20261103 [--match amendment,referendum]
 *
 * --match is a comma-separated list of plain keywords; a race is fetched when
 * its name contains any of them (case-insensitive substring, no regular
 * expression is built from the argument).
 *
 * Writes one <prefix>_<race-slug>.txt per matching race (page innerText)
 * plus the raw HTML alongside, and prints the statewide YES/NO block of each
 * so the run can be eyeballed against the portal. Nothing here is parsed:
 * parsing is the tested loader's job, with its Total-row integrity check.
 */
const { chromium } = require("playwright");
const fs = require("fs");
const path = require("path");

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : fallback;
}

const OUT = arg("out", "data/raw");
const PREFIX = arg("prefix", "enr_mo");
const KEYWORDS = arg("match", "amendment,proposition,referendum,question")
  .split(",")
  .map((k) => k.trim().toLowerCase())
  .filter(Boolean);
const matches = (text) => KEYWORDS.some((k) => text.toLowerCase().includes(k));
const UA =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36";

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
    args: ["--disable-blink-features=AutomationControlled"],
  });
  const ctx = await browser.newContext({
    userAgent: UA,
    viewport: { width: 1366, height: 860 },
    locale: "en-US",
    timezoneId: "America/Chicago",
  });
  await ctx.addInitScript(() => {
    Object.defineProperty(navigator, "webdriver", { get: () => undefined });
  });
  const page = await ctx.newPage();
  try {
    await page.goto("https://enr.sos.mo.gov/default.aspx", { waitUntil: "load", timeout: 60000 });
    await page.waitForTimeout(5000);
    const banner = (await page.innerText("body")).match(/(Official|Unofficial) Results[^\n]*\n[^\n]*/);
    console.log("portal says:", banner ? banner[0].replace(/\n/g, " | ") : "(no status banner found)");
    await page.click("a:has-text('Pick a Race')");
    await page.waitForLoadState("load");
    await page.waitForTimeout(5000);
    const options = await page.$$eval("#cboRaces option", (os) =>
      os.map((o) => ({ value: o.value, text: o.text.trim() })),
    );
    const races = options.filter((o) => matches(o.text));
    console.log(`${races.length} race(s) match [${KEYWORDS.join(", ")}] out of ${options.length}`);
    for (const race of races) {
      await page.selectOption("#cboRaces", race.value);
      await page.waitForTimeout(1500);
      await page.click("#MainContent_btnCountyChange");
      try {
        await page.waitForFunction(() => /County\tYES\tNO|County\s+YES\s+NO/.test(document.body.innerText), null, {
          timeout: 30000,
        });
      } catch {
        console.log(`  ! no county table appeared for "${race.text}"`);
      }
      await page.waitForTimeout(3000);
      const body = await page.innerText("body");
      const slug = race.text.replace(/[^A-Za-z0-9]+/g, "_").replace(/^_|_$/g, "").toLowerCase();
      fs.writeFileSync(path.join(OUT, `${PREFIX}_${slug}.txt`), body);
      fs.writeFileSync(path.join(OUT, `${PREFIX}_${slug}.html`), await page.content());
      const statewide = body.match(/\tYES\t[\d,]+\t[\d.]+%[\s\S]*?\tNO\t[\d,]+\t[\d.]+%/);
      console.log(`  ${race.text}: ${statewide ? statewide[0].replace(/\s+/g, " ").trim() : "(statewide block not found)"}`);
    }
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.error("fetch_mo_enr failed:", e.message);
  process.exit(1);
});
