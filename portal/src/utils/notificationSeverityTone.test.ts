import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  NOTIFICATION_TYPE_OPTIONS,
  resolveNotificationSeverityTone,
} from "./notificationSeverityTone";

describe("resolveNotificationSeverityTone", () => {
  it("mapeia contrato EN e aliases PT", () => {
    assert.equal(resolveNotificationSeverityTone("info").tone, "info");
    assert.equal(resolveNotificationSeverityTone("aviso").labelPt, "Aviso");
    assert.equal(resolveNotificationSeverityTone("atenção").tone, "warning");
    assert.equal(resolveNotificationSeverityTone("alerta").tone, "error");
    assert.equal(resolveNotificationSeverityTone("alerta").attentionEyebrow, "Alerta importante");
    assert.equal(resolveNotificationSeverityTone("unknown").tone, "info");
  });

  it("oferece opções admin com valor EN", () => {
    assert.deepEqual(
      NOTIFICATION_TYPE_OPTIONS.map((item) => item.value),
      ["info", "success", "warning", "error"],
    );
  });
});
