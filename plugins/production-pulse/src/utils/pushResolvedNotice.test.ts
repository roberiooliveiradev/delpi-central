import { describe, expect, it, vi } from "vitest";

import { ProductionPulseRequestError } from "../api/httpClient";
import {
  otaActiveNoticeId,
  otaJobCreatedNoticeId,
  pushResolvedProductionPulseNotice,
} from "./pushResolvedNotice";

describe("ota notice ids", () => {
  it("builds deterministic active and created ids", () => {
    expect(otaActiveNoticeId("dev-1")).toBe("ota-target-active:dev-1");
    expect(otaJobCreatedNoticeId("job-9")).toBe("ota-job-created:job-9");
  });
});

describe("pushResolvedProductionPulseNotice", () => {
  it("upserts openTargetExists as operational notice with id and action", () => {
    const push = vi.fn();
    const err = new ProductionPulseRequestError(
      "O dispositivo já possui uma atualização OTA em andamento.",
      409,
      "openTargetExists",
    );
    const resolved = pushResolvedProductionPulseNotice(push, err, {
      id: otaActiveNoticeId("dev-1"),
      onAction: () => undefined,
    });
    expect(resolved?.code).toBe("openTargetExists");
    expect(push).toHaveBeenCalledTimes(1);
    expect(push.mock.calls[0][0]).toMatchObject({
      id: "ota-target-active:dev-1",
      variant: "warning",
      action: { label: expect.any(String) },
    });
  });

  it("does not push structural api_unavailable to floating notices", () => {
    const push = vi.fn();
    const err = new ProductionPulseRequestError("down", 503, "api_unavailable");
    const resolved = pushResolvedProductionPulseNotice(push, err);
    expect(resolved?.surface).toBe("structural");
    expect(push).not.toHaveBeenCalled();
  });
});
