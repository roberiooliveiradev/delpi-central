/**
 * Browser execution host — Chromium via Playwright.
 *
 * Stateless: one shared browser process, a fresh incognito context per
 * render. Network is locked to (a) this worker's own loopback render page
 * and (b) the tv-dashboard-api origin for canonical media URLs — everything
 * else is aborted. No arbitrary navigation is possible.
 */

import { chromium, type Browser } from "playwright";
import type { RenderRequest } from "./contract.js";

export type RenderFailureCode =
  | "RENDER_TIMEOUT"
  | "RENDER_FAILED"
  | "RENDER_BUSY"
  | "UNSUPPORTED_EXTERNAL_CONTENT"
  | "SLIDE_NOT_IN_PAYLOAD";

export class RenderError extends Error {
  constructor(
    readonly code: RenderFailureCode | string,
    message: string,
  ) {
    super(message);
  }
}

export type RenderWorkerOptions = {
  /** Loopback base URL serving the bundled render page (this server). */
  selfOrigin: string;
  /** Internal origin of tv-dashboard-api for canonical media URLs. */
  apiOrigin: string;
  /** Root path of tv-dashboard-api (media URL prefix inside the payload). */
  apiRootPath: string;
  /** Max concurrent renders. */
  concurrency: number;
  /** Per-render timeout in ms (includes paint waits). */
  timeoutMs: number;
};

const DEFAULT_VIEWPORT = { width: 1920, height: 1080 };

/**
 * Canonical viewport declared by the pushed payload's playlist — the
 * authoritative paint size (tv-dashboard-api resolves it via
 * resolve_effective_viewport_px before pushing).
 */
function canonicalViewport(
  presentation: Record<string, unknown>,
): { width: number; height: number } | null {
  const playlist = presentation.playlist;
  if (typeof playlist !== "object" || playlist === null) return null;
  const { viewportWidth, viewportHeight } = playlist as Record<string, unknown>;
  if (
    typeof viewportWidth === "number" &&
    typeof viewportHeight === "number" &&
    Number.isInteger(viewportWidth) &&
    Number.isInteger(viewportHeight) &&
    viewportWidth >= 16 &&
    viewportHeight >= 16 &&
    viewportWidth <= 8192 &&
    viewportHeight <= 8192
  ) {
    return { width: viewportWidth, height: viewportHeight };
  }
  return null;
}

export class RenderWorker {
  private browser: Browser | null = null;
  private launching: Promise<Browser> | null = null;
  private inflight = 0;
  private readonly queue: Array<() => void> = [];

  constructor(private readonly options: RenderWorkerOptions) {}

  private async ensureBrowser(): Promise<Browser> {
    if (this.browser?.isConnected()) return this.browser;
    if (!this.launching) {
      this.launching = chromium
        .launch({
          headless: true,
          args: [
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--force-color-profile=srgb",
          ],
        })
        .then((browser) => {
          browser.on("disconnected", () => {
            this.browser = null;
          });
          this.browser = browser;
          return browser;
        })
        .finally(() => {
          this.launching = null;
        });
    }
    return this.launching;
  }

  private async acquire(): Promise<void> {
    if (this.inflight < this.options.concurrency) {
      this.inflight += 1;
      return;
    }
    await new Promise<void>((resolve, reject) => {
      const timer = setTimeout(
        () => reject(new RenderError("RENDER_BUSY", "render queue saturated")),
        this.options.timeoutMs,
      );
      this.queue.push(() => {
        clearTimeout(timer);
        this.inflight += 1;
        resolve();
      });
    });
  }

  private release() {
    this.inflight -= 1;
    const next = this.queue.shift();
    if (next) next();
  }

  async health(): Promise<boolean> {
    try {
      await this.ensureBrowser();
      return true;
    } catch {
      return false;
    }
  }

  /** Render the target slide of a canonical presentation payload to PNG. */
  async render(request: RenderRequest): Promise<Buffer> {
    await this.acquire();
    // The canonical payload's playlist viewport is authoritative; the request
    // viewport is only a fallback hint for payloads that omit it.
    const viewport =
      canonicalViewport(request.presentation) ?? request.viewport ?? DEFAULT_VIEWPORT;
    try {
      const browser = await this.ensureBrowser();
      const context = await browser.newContext({
        viewport,
        deviceScaleFactor: 1,
        // Defense-in-depth: page scripts never navigate; all requests go
        // through the allowlist route below.
      });
      try {
        const apiRoot = this.options.apiRootPath.replace(/\/$/, "");
        const apiOrigin = new URL(this.options.apiOrigin).origin;
        const selfOrigin = new URL(this.options.selfOrigin).origin;
        await context.route("**/*", (route) => {
          const url = new URL(route.request().url());
          if (url.origin === selfOrigin && url.pathname.startsWith(`${apiRoot}/`)) {
            // Canonical media URL relative to the API root — rewrite to the
            // internal service origin. Same path, read-only media endpoints.
            return route.continue({ url: `${apiOrigin}${url.pathname}${url.search}` });
          }
          if (url.origin === selfOrigin) return route.continue();
          return route.abort("blockedbyclient");
        });
        const page = await context.newPage();
        page.setDefaultTimeout(this.options.timeoutMs);
        await page.goto(`${selfOrigin}/render-page/index.html`, {
          waitUntil: "load",
          timeout: this.options.timeoutMs,
        });
        const result = (await page.evaluate(async (input) => {
          // Runs inside the page — `window` is DOM-side; keep it untyped here.
          const fn = (globalThis as Record<string, unknown>).__tvRenderSlide as
            | ((arg: unknown) => Promise<{ ok: boolean; code?: string }>)
            | undefined;
          if (typeof fn !== "function") return { ok: false, code: "RENDER_PAGE_NOT_READY" };
          return fn(input);
        }, { presentation: request.presentation, slideId: request.slideId })) as
          | { ok: true; width: number; height: number }
          | { ok: false; code: string };
        if (!result.ok) {
          throw new RenderError(result.code, `render page failed: ${result.code}`);
        }
        const stage = page.locator("#tv-render-root");
        const png = await stage.screenshot({ type: "png", timeout: this.options.timeoutMs });
        return png;
      } finally {
        await context.close().catch(() => undefined);
      }
    } catch (error) {
      if (error instanceof RenderError) throw error;
      const message = error instanceof Error ? error.message : String(error);
      const code = /timeout/i.test(message) ? "RENDER_TIMEOUT" : "RENDER_FAILED";
      throw new RenderError(code, message.slice(0, 300));
    } finally {
      this.release();
    }
  }

  async close() {
    await this.browser?.close().catch(() => undefined);
    this.browser = null;
  }
}
