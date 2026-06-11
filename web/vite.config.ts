import { defineConfig } from "vite";

// GitHub Pages serves the app under /geo-fluid-dynamics-engine/. The base
// is injected at build time (deploy workflow and the E2E webServer both set
// GFDE_BASE) — and every runtime fetch uses import.meta.env.BASE_URL, so the
// sub-path works end to end. This pairing is the fix for the prior project's
// Bug #8 (blank map on Pages from absolute /data/... paths).
export default defineConfig({
  base: process.env.GFDE_BASE ?? "/",
});
