/**
 * Bounded internal HTTP surface for the TV canonical render worker.
 *
 * Routes:
 *   GET  /healthz              → liveness
 *   POST /render               → Bearer(service token) + bounded JSON contract
 *                                → image/png | typed JSON error
 *   GET  /render-page/*        → loopback-only static render bundle
 *
 * This is not a public API: only tv-dashboard-api calls /render, with a
 * shared service token, inside the internal network.
 */

import { createServer, type IncomingMessage, type ServerResponse } from "node:http";
import { createReadStream, existsSync, statSync } from "node:fs";
import path from "node:path";
import { timingSafeEqual } from "node:crypto";
import { fileURLToPath } from "node:url";
import {
  RENDER_REQUEST_MAX_BYTES,
  validateRenderRequest,
} from "./contract.js";
import { RenderError, RenderWorker } from "./render.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
// Built bundle only — src/ when running under tsx, dist/ when compiled; both
// resolve to <pkg>/dist/render-page. Source HTML is never served.
const PAGE_DIR = path.resolve(__dirname, "..", "dist", "render-page");

export type ServerConfig = {
  port: number;
  serviceToken: string;
  apiOrigin: string;
  apiRootPath: string;
  concurrency: number;
  timeoutMs: number;
};

export function loadConfig(env: NodeJS.ProcessEnv = process.env): ServerConfig {
  return {
    port: Number(env.RENDER_WORKER_PORT || 8100),
    serviceToken: env.TV_RENDER_WORKER_SERVICE_TOKEN ?? "",
    apiOrigin: env.TV_DASHBOARD_API_INTERNAL_URL ?? "http://tv-dashboard-api:8000",
    apiRootPath: env.TV_DASHBOARD_API_ROOT_PATH ?? "/apps/tv-dashboard-api",
    concurrency: Math.max(1, Number(env.RENDER_WORKER_CONCURRENCY || 2)),
    timeoutMs: Math.max(1_000, Number(env.RENDER_WORKER_TIMEOUT_MS || 30_000)),
  };
}

function writeJson(res: ServerResponse, status: number, body: unknown) {
  const payload = JSON.stringify(body);
  res.writeHead(status, {
    "content-type": "application/json; charset=utf-8",
    "content-length": Buffer.byteLength(payload),
  });
  res.end(payload);
}

function authorized(req: IncomingMessage, token: string): boolean {
  if (!token) return false;
  const header = String(req.headers.authorization ?? "");
  const expected = `Bearer ${token}`;
  const a = Buffer.from(header);
  const b = Buffer.from(expected);
  return a.length === b.length && timingSafeEqual(a, b);
}

const STATIC_MIME: Record<string, string> = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".map": "application/json",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".woff2": "font/woff2",
};

function serveStatic(req: IncomingMessage, res: ServerResponse) {
  // Loopback-only consumer (the worker's own Chromium). Path is normalized
  // and must stay inside PAGE_DIR — traversal rejects.
  const url = new URL(req.url ?? "/", "http://127.0.0.1");
  const rel = decodeURIComponent(url.pathname.replace(/^\/render-page\/?/, ""));
  const file = path.resolve(PAGE_DIR, rel || "index.html");
  if (!file.startsWith(PAGE_DIR) || !existsSync(file) || !statSync(file).isFile()) {
    return writeJson(res, 404, { status: "error", code: "NOT_FOUND" });
  }
  res.writeHead(200, {
    "content-type": STATIC_MIME[path.extname(file)] ?? "application/octet-stream",
    "cache-control": "no-store",
  });
  createReadStream(file).pipe(res);
}

function readBody(req: IncomingMessage): Promise<Buffer> {
  return new Promise((resolve, reject) => {
    const declared = Number(req.headers["content-length"] ?? 0);
    if (declared > RENDER_REQUEST_MAX_BYTES) {
      req.resume();
      return reject(new RenderError("PAYLOAD_TOO_LARGE", "body over limit"));
    }
    const chunks: Buffer[] = [];
    let size = 0;
    req.on("data", (chunk: Buffer) => {
      size += chunk.length;
      if (size > RENDER_REQUEST_MAX_BYTES) {
        req.destroy();
        reject(new RenderError("PAYLOAD_TOO_LARGE", "body over limit"));
      } else {
        chunks.push(chunk);
      }
    });
    req.on("end", () => resolve(Buffer.concat(chunks)));
    req.on("error", reject);
  });
}

export function createRenderServer(config: ServerConfig, worker: RenderWorker) {
  const startedAt = Date.now();

  return createServer(async (req, res) => {
    const url = new URL(req.url ?? "/", "http://127.0.0.1");
    try {
      if (req.method === "GET" && url.pathname === "/healthz") {
        return writeJson(res, 200, {
          status: "ok",
          uptimeSec: Math.round((Date.now() - startedAt) / 1000),
          browser: await worker.health(),
        });
      }

      if (req.method === "GET" && url.pathname.startsWith("/render-page")) {
        return serveStatic(req, res);
      }

      if (req.method === "POST" && url.pathname === "/render") {
        if (!config.serviceToken) {
          return writeJson(res, 503, {
            status: "error",
            code: "RENDER_WORKER_DISABLED",
            message: "service token not configured",
          });
        }
        if (!authorized(req, config.serviceToken)) {
          return writeJson(res, 401, {
            status: "error",
            code: "UNAUTHORIZED",
            message: "invalid service token",
          });
        }
        const contentType = String(req.headers["content-type"] ?? "").split(";")[0].trim();
        if (contentType !== "application/json") {
          return writeJson(res, 415, {
            status: "error",
            code: "INVALID_REQUEST",
            message: "content-type must be application/json",
          });
        }
        let raw: Buffer;
        try {
          raw = await readBody(req);
        } catch (error) {
          const code = error instanceof RenderError ? error.code : "INVALID_REQUEST";
          return writeJson(res, 413, { status: "error", code });
        }
        let parsed: unknown;
        try {
          parsed = JSON.parse(raw.toString("utf-8"));
        } catch {
          return writeJson(res, 422, {
            status: "error",
            code: "INVALID_REQUEST",
            message: "body must be JSON",
          });
        }
        const validated = validateRenderRequest(parsed);
        if (!validated.ok) {
          return writeJson(res, 422, { status: "error", ...validated.error });
        }
        try {
          const png = await worker.render(validated.value);
          res.writeHead(200, {
            "content-type": "image/png",
            "content-length": png.length,
            "x-render-revision": String(validated.value.revision),
          });
          return res.end(png);
        } catch (error) {
          if (error instanceof RenderError) {
            const status =
              error.code === "UNSUPPORTED_EXTERNAL_CONTENT"
                ? 422
                : error.code === "RENDER_BUSY"
                  ? 429
                  : error.code === "RENDER_TIMEOUT"
                    ? 504
                    : 500;
            return writeJson(res, status, {
              status: "error",
              code: error.code,
              message: error.message,
            });
          }
          throw error;
        }
      }

      return writeJson(res, 404, { status: "error", code: "NOT_FOUND" });
    } catch (error) {
      // Never leak internals; safe metadata only.
      console.error("render_worker_unhandled", error instanceof Error ? error.message : error);
      return writeJson(res, 500, {
        status: "error",
        code: "RENDER_FAILED",
        message: "internal error",
      });
    }
  });
}

export async function main() {
  const config = loadConfig();
  const worker = new RenderWorker({
    selfOrigin: `http://127.0.0.1:${config.port}`,
    apiOrigin: config.apiOrigin,
    apiRootPath: config.apiRootPath,
    concurrency: config.concurrency,
    timeoutMs: config.timeoutMs,
  });
  const server = createRenderServer(config, worker);
  server.listen(config.port, "0.0.0.0", () => {
    console.log(
      `tv-dashboard-render-worker listening :${config.port} (concurrency=${config.concurrency})`,
    );
  });
  const shutdown = async () => {
    server.close();
    await worker.close();
    process.exit(0);
  };
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

const isMain = process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1]);
if (isMain) {
  void main();
}
