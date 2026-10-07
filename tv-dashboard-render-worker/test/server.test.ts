import { afterAll, beforeAll, describe, expect, it } from "vitest";
import type { AddressInfo } from "node:net";
import { createRenderServer, loadConfig, type ServerConfig } from "../src/server.js";
import { RenderWorker } from "../src/render.js";

const CONFIG: ServerConfig = {
  port: 0,
  serviceToken: "test-service-token",
  apiOrigin: "http://tv-dashboard-api:8000",
  apiRootPath: "/apps/tv-dashboard-api",
  concurrency: 1,
  timeoutMs: 5000,
};

let server: ReturnType<typeof createRenderServer>;
let base: string;

// Fake worker — never launches a browser; contract tests only.
const fakeWorker = {
  health: async () => true,
  render: async () => Buffer.from([0x89, 0x50, 0x4e, 0x47]),
  close: async () => undefined,
} as unknown as RenderWorker;

beforeAll(async () => {
  server = createRenderServer(CONFIG, fakeWorker);
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  base = `http://127.0.0.1:${(server.address() as AddressInfo).port}`;
});

afterAll(async () => {
  await new Promise((resolve) => server.close(resolve));
});

describe("render worker http surface", () => {
  it("healthz responds", async () => {
    const res = await fetch(`${base}/healthz`);
    expect(res.status).toBe(200);
    const body = await res.json();
    expect(body.status).toBe("ok");
    expect(body.browser).toBe(true);
  });

  it("rejects render without service token", async () => {
    const res = await fetch(`${base}/render`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({}),
    });
    expect(res.status).toBe(401);
  });

  it("rejects render with wrong token", async () => {
    const res = await fetch(`${base}/render`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: "Bearer wrong",
      },
      body: JSON.stringify({}),
    });
    expect(res.status).toBe(401);
  });

  it("rejects the platform API_DELPI token when it differs from the dedicated worker token", async () => {
    // Negative: no credential reuse — a valid platform S2S token must NOT
    // authenticate the worker when the dedicated secret differs.
    const res = await fetch(`${base}/render`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: "Bearer api-delpi-internal-token",
      },
      body: JSON.stringify({}),
    });
    expect(res.status).toBe(401);
  });

  it("rejects non-json content type", async () => {
    const res = await fetch(`${base}/render`, {
      method: "POST",
      headers: {
        "content-type": "text/plain",
        authorization: `Bearer ${CONFIG.serviceToken}`,
      },
      body: "{}",
    });
    expect(res.status).toBe(415);
  });

  it("rejects forbidden fields", async () => {
    const res = await fetch(`${base}/render`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${CONFIG.serviceToken}`,
      },
      body: JSON.stringify({ url: "https://evil.test" }),
    });
    expect(res.status).toBe(422);
    const body = await res.json();
    expect(body.code).toBe("FORBIDDEN_FIELD");
  });

  it("renders a valid bounded request", async () => {
    const res = await fetch(`${base}/render`, {
      method: "POST",
      headers: {
        "content-type": "application/json",
        authorization: `Bearer ${CONFIG.serviceToken}`,
      },
      body: JSON.stringify({
        playlistId: "pl-1",
        slideId: "sl-1",
        revision: 3,
        presentation: {
          playlist: { id: "pl-1" },
          presentationMeta: { revision: 3 },
          slides: [{ id: "sl-1" }],
        },
      }),
    });
    expect(res.status).toBe(200);
    expect(res.headers.get("content-type")).toBe("image/png");
    expect(res.headers.get("x-render-revision")).toBe("3");
  });

  it("unknown routes 404", async () => {
    const res = await fetch(`${base}/anything`);
    expect(res.status).toBe(404);
  });
});

describe("loadConfig", () => {
  it("reads bounded env config", () => {
    const cfg = loadConfig({
      RENDER_WORKER_PORT: "9100",
      TV_RENDER_WORKER_SERVICE_TOKEN: "tok",
      RENDER_WORKER_CONCURRENCY: "4",
      RENDER_WORKER_TIMEOUT_MS: "100",
    } as NodeJS.ProcessEnv);
    expect(cfg.port).toBe(9100);
    expect(cfg.concurrency).toBe(4);
    expect(cfg.timeoutMs).toBe(1000); // floor
  });
});
