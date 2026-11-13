import { describe, expect, it } from "vitest";
import {
  isLnfForbiddenRoom,
  isLnfQueueReconciled,
  isLnfRequestChanged,
  isLnfUnmappedProductsChanged,
  isQueueRefetchEvent,
} from "./events";
import {
  branchRoom,
  encodeLnfSubscribe,
  encodeLnfUnsubscribe,
  requestRoom,
  unmappedProductsRoom,
} from "./rooms";

describe("lnf realtime rooms and events", () => {
  it("monta nomes de sala", () => {
    expect(branchRoom("01")).toBe("lnf:branch:01");
    expect(requestRoom(" abc ")).toBe("lnf:request:abc");
    expect(unmappedProductsRoom()).toBe("lnf:unmapped-products");
  });

  it("encode subscribe/unsubscribe", () => {
    expect(JSON.parse(encodeLnfSubscribe("lnf:branch:01"))).toEqual({
      type: "subscribe",
      room: "lnf:branch:01",
    });
    expect(JSON.parse(encodeLnfUnsubscribe("lnf:branch:01"))).toEqual({
      type: "unsubscribe",
      room: "lnf:branch:01",
    });
  });

  it("type guards", () => {
    expect(
      isLnfRequestChanged({
        type: "lnf.request.changed",
        eventId: "e1",
        branch: "01",
        requestId: "r1",
        reason: "updated",
      }),
    ).toBe(true);
    expect(
      isLnfQueueReconciled({
        type: "lnf.queue.reconciled",
        eventId: "e2",
        branch: "01",
        updatedCount: 2,
      }),
    ).toBe(true);
    expect(
      isLnfUnmappedProductsChanged({
        type: "lnf.unmapped-products.changed",
        eventId: "e3",
      }),
    ).toBe(true);
    expect(isLnfForbiddenRoom({ type: "error", code: "forbidden_room" })).toBe(
      true,
    );
  });

  it("isQueueRefetchEvent filtra pela filial", () => {
    expect(
      isQueueRefetchEvent(
        {
          type: "lnf.request.changed",
          eventId: "e1",
          branch: "01",
          requestId: "r1",
          reason: "updated",
        },
        "01",
      ),
    ).toBe(true);
    expect(
      isQueueRefetchEvent(
        {
          type: "lnf.request.changed",
          eventId: "e1",
          branch: "02",
          requestId: "r1",
          reason: "updated",
        },
        "01",
      ),
    ).toBe(false);
  });
});
