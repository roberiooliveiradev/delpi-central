import { describe, expect, it } from "vitest";

import { INITIAL_ADMIN_HUB_UI } from "./adminHubUiState";
import {
  noticeAffectsLayers,
  transitionAdminHub,
} from "./adminHubLayerTransitions";

const device = { type: "device" as const, id: "d1" };
const firmware = { type: "firmware" as const, id: "f1" };

describe("transitionAdminHub", () => {
  it("none → summary closes conflicting layers and omits entity from URL", () => {
    const next = transitionAdminHub(INITIAL_ADMIN_HUB_UI, {
      type: "openSummary",
      entity: device,
      popoverNodeId: "dev:d1",
    });
    expect(next.state.openLayer).toBe("summary");
    expect(next.state.selectedEntity).toEqual(device);
    expect(next.state.modal).toBeNull();
    expect(next.state.panel).toBeNull();
    expect(next.state.popoverAnchorId).toBe("dev:d1");
    expect(next.urlSlice.entity).toBeNull();
    expect(next.urlSlice.modal).toBeNull();
    expect(next.syncUrl).toBe(true);
  });

  it("summary → menu keeps entity, clears modal, does not put entity in URL", () => {
    const base = transitionAdminHub(INITIAL_ADMIN_HUB_UI, {
      type: "openSummary",
      entity: device,
      popoverNodeId: "dev:d1",
    }).state;
    const next = transitionAdminHub(base, {
      type: "openEntityMenu",
      entity: device,
      popoverNodeId: "dev:d1",
    });
    expect(next.state.openLayer).toBe("menu");
    expect(next.state.selectedEntity).toEqual(device);
    expect(next.urlSlice.entity).toBeNull();
  });

  it("menu → modal clears ephemeral anchor and sets modal URL", () => {
    const menu = transitionAdminHub(INITIAL_ADMIN_HUB_UI, {
      type: "openEntityMenu",
      entity: device,
      popoverNodeId: "dev:d1",
    }).state;
    const next = transitionAdminHub(menu, {
      type: "openModal",
      modal: "device-detail",
      entity: device,
    });
    expect(next.state.openLayer).toBe("modal");
    expect(next.state.modal).toBe("device-detail");
    expect(next.state.popoverAnchorId).toBeNull();
    expect(next.clearAnchor).toBe(true);
    expect(next.urlSlice.modal).toBe("device-detail");
    expect(next.urlSlice.entity).toBe("device:d1");
  });

  it("menu → confirm → closeConfirm restores modal when present", () => {
    let state = transitionAdminHub(INITIAL_ADMIN_HUB_UI, {
      type: "openModal",
      modal: "device-edit",
      entity: device,
    }).state;
    state = transitionAdminHub(state, {
      type: "openConfirm",
      kind: "disable-device",
      id: "d1",
    }).state;
    expect(state.openLayer).toBe("confirm");
    const closed = transitionAdminHub(state, { type: "closeConfirm" });
    expect(closed.state.openLayer).toBe("modal");
    expect(closed.state.modal).toBe("device-edit");
    expect(closed.urlSlice.modal).toBe("device-edit");
  });

  it("closeModal clears modal from URL and does not reopen", () => {
    const open = transitionAdminHub(INITIAL_ADMIN_HUB_UI, {
      type: "openModal",
      modal: "device-create",
    }).state;
    const closed = transitionAdminHub(open, { type: "closeModal" });
    expect(closed.state.openLayer).toBe("none");
    expect(closed.state.modal).toBeNull();
    expect(closed.urlSlice.modal).toBeNull();
    expect(closed.urlSlice.entity).toBeNull();
  });

  it("panel → modal → closeModal without restore leaves none", () => {
    let state = transitionAdminHub(INITIAL_ADMIN_HUB_UI, {
      type: "openPanel",
      panel: "jobs",
    }).state;
    state = transitionAdminHub(state, {
      type: "openModal",
      modal: "job-detail",
      entity: { type: "job", id: "j1" },
    }).state;
    const closed = transitionAdminHub(state, { type: "closeModal" });
    expect(closed.state.openLayer).toBe("none");
    expect(closed.state.panel).toBeNull();
  });

  it("openPanel drivers sets panel URL and clears modal", () => {
    const next = transitionAdminHub(INITIAL_ADMIN_HUB_UI, {
      type: "openPanel",
      panel: "drivers",
    });
    expect(next.state.openLayer).toBe("panel");
    expect(next.state.panel).toBe("drivers");
    expect(next.state.modal).toBeNull();
    expect(next.urlSlice.panel).toBe("drivers");
    expect(next.urlSlice.modal).toBeNull();
  });

  it("openModal driver-create / driver-detail share entity in URL", () => {
    const created = transitionAdminHub(INITIAL_ADMIN_HUB_UI, {
      type: "openModal",
      modal: "driver-create",
    });
    expect(created.state.modal).toBe("driver-create");
    expect(created.urlSlice.modal).toBe("driver-create");

    const detail = transitionAdminHub(INITIAL_ADMIN_HUB_UI, {
      type: "openModal",
      modal: "driver-detail",
      entity: { type: "driver", id: "esp8266_counter_v1" },
    });
    expect(detail.state.selectedEntity).toEqual({
      type: "driver",
      id: "esp8266_counter_v1",
    });
    expect(detail.urlSlice.entity).toBe("driver:esp8266_counter_v1");
    expect(detail.urlSlice.modal).toBe("driver-detail");
  });

  it("hydrateFromUrl does not reopen summary from stale entity", () => {
    const afterClose = transitionAdminHub(
      transitionAdminHub(INITIAL_ADMIN_HUB_UI, {
        type: "openSummary",
        entity: device,
        popoverNodeId: "dev:d1",
      }).state,
      { type: "closeTransient" },
    ).state;
    expect(afterClose.openLayer).toBe("none");
    const hydrated = transitionAdminHub(afterClose, {
      type: "hydrateFromUrl",
      entity: device,
      panel: null,
      modal: null,
    });
    expect(hydrated.state.openLayer).toBe("none");
    expect(hydrated.syncUrl).toBe(false);
  });

  it("hydrateFromUrl does not clobber open menu when URL has no modal/panel", () => {
    const menu = transitionAdminHub(INITIAL_ADMIN_HUB_UI, {
      type: "openEntityMenu",
      entity: firmware,
      popoverNodeId: "fw:k1",
    }).state;
    const hydrated = transitionAdminHub(menu, {
      type: "hydrateFromUrl",
      entity: firmware,
      panel: null,
      modal: null,
    });
    expect(hydrated.state.openLayer).toBe("menu");
  });

  it("hydrateFromUrl preserves confirm over modal URL projection", () => {
    let state = transitionAdminHub(INITIAL_ADMIN_HUB_UI, {
      type: "openModal",
      modal: "device-edit",
      entity: device,
    }).state;
    state = transitionAdminHub(state, {
      type: "openConfirm",
      kind: "unlink",
      id: "d1",
    }).state;
    const hydrated = transitionAdminHub(state, {
      type: "hydrateFromUrl",
      entity: device,
      panel: null,
      modal: "device-edit",
    });
    expect(hydrated.state.openLayer).toBe("confirm");
    expect(hydrated.state.confirm?.kind).toBe("unlink");
  });

  it("graphReloading clears ephemeral summary/menu anchors (H1)", () => {
    const summary = transitionAdminHub(INITIAL_ADMIN_HUB_UI, {
      type: "openSummary",
      entity: device,
      popoverNodeId: "dev:d1",
    }).state;
    const next = transitionAdminHub(summary, { type: "graphReloading" });
    expect(next.state.openLayer).toBe("none");
    expect(next.clearAnchor).toBe(true);
    expect(next.state.popoverAnchorId).toBeNull();
  });

  it("rapid summary → menu → modal stays coherent", () => {
    let state = INITIAL_ADMIN_HUB_UI;
    state = transitionAdminHub(state, {
      type: "openSummary",
      entity: device,
      popoverNodeId: "dev:d1",
    }).state;
    state = transitionAdminHub(state, {
      type: "openEntityMenu",
      entity: device,
      popoverNodeId: "dev:d1",
    }).state;
    state = transitionAdminHub(state, {
      type: "openModal",
      modal: "ota-schedule",
      entity: device,
    }).state;
    expect(state.openLayer).toBe("modal");
    expect(state.modal).toBe("ota-schedule");
    expect(state.confirm).toBeNull();
  });

  it("noticeAffectsLayers is always false", () => {
    expect(noticeAffectsLayers()).toBe(false);
  });
});
