import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

describe("my-requests realtime wiring", () => {
  it("App mounts RealtimeProvider under FloatingNotice", () => {
    const app = readFileSync(join(root, "App.tsx"), "utf8");
    expect(app).toContain("MyRequestsRealtimeProvider");
    expect(app).toContain("MyRequestsFloatingNoticeProvider");
    expect(app.indexOf("MyRequestsFloatingNoticeProvider")).toBeLessThan(
      app.indexOf("MyRequestsRealtimeProvider"),
    );
  });

  it("lists and detail sync via realtime hooks", () => {
    const mine = readFileSync(join(root, "pages/MinePage.tsx"), "utf8");
    const queue = readFileSync(join(root, "pages/WorkQueuePage.tsx"), "utf8");
    const detail = readFileSync(join(root, "pages/RequestDetailPage.tsx"), "utf8");
    expect(mine).toContain("useMyRequestsListSync");
    expect(queue).toContain("useMyRequestsListSync");
    expect(detail).toContain("useMyRequestsDetailSync");
    expect(detail).toContain("refreshKey={timelineEpoch}");
  });

  it("http client sends X-My-Requests-Client-Id", () => {
    const http = readFileSync(join(root, "api/httpClient.ts"), "utf8");
    expect(http).toContain("MY_REQUESTS_CLIENT_ID_HEADER");
    expect(http).toContain("getMyRequestsClientId");
  });
});
