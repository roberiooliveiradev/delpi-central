import { describe, expect, it } from "vitest";

import {
  buildMyRequestsRealtimeWsUrl,
  buildRequestSubscribePayload,
  parseMyRequestsRealtimeEvent,
  resolveRemoteNotification,
} from "./realtime";

describe("my-requests realtime protocol", () => {
  it("builds ws url with token and client_id", () => {
    const url = buildMyRequestsRealtimeWsUrl({
      token: "tok",
      clientId: "cid-1",
    });
    expect(url).toContain("/apps/requests-api/v1/realtime/ws");
    expect(url).toContain("token=tok");
    expect(url).toContain("client_id=cid-1");
  });

  it("parses known events and rejects garbage", () => {
    expect(
      parseMyRequestsRealtimeEvent(
        JSON.stringify({ type: "request.changed", requestId: "r1" }),
      )?.type,
    ).toBe("request.changed");
    expect(parseMyRequestsRealtimeEvent("not-json")).toBeNull();
  });

  it("builds subscribe payload and resolves notification", () => {
    expect(JSON.parse(buildRequestSubscribePayload("rid"))).toEqual({
      type: "subscribe",
      requestId: "rid",
    });
    const notice = resolveRemoteNotification({
      type: "request.changed",
      requestId: "r1",
      notification: {
        title: "Atualizada",
        message: "Status novo",
        variant: "info",
      },
    });
    expect(notice?.title).toBe("Atualizada");
    expect(
      resolveRemoteNotification({ type: "request.changed", requestId: "r1" }),
    ).toBeNull();
  });
});
