import assert from "node:assert/strict";
import { describe, it } from "node:test";

import type {
  PortalTourCatalogResponse,
  PortalTourProgressResponse,
} from "../data/coreApi.ts";
import { resolvePortalTourHomeEntryState } from "./portalTourHomeEntry.ts";
import {
  isPortalTourDismissed,
  shouldActivatePortalTourSession,
  shouldAutoOpenPortalTourPanel,
} from "./portalTourPersistence.ts";

const CATALOG: PortalTourCatalogResponse = {
  tourVersion: "2026-08-portal-v7-notification-channels",
  quests: [],
  requiredQuestIds: [
    "open-apps",
    "pin-app",
    "sidebar-logo-home",
    "sidebar-notifications",
    "sidebar-profile",
    "sidebar-theme",
  ],
  optionalQuestIds: [],
  newQuestIds: [],
  progressPercent: 0,
  explorerLevel: "Explorador",
  earnedXp: 0,
  categoryLabels: {},
  categoryOrder: [],
};

function progress(
  partial: Partial<PortalTourProgressResponse>,
): PortalTourProgressResponse {
  return {
    tourVersion: "2026-08-portal-v7-notification-channels",
    status: "exploring",
    completedQuestIds: [],
    startedAt: null,
    lastActivityAt: null,
    completedAt: null,
    insights: null,
    ...partial,
  };
}

describe("shouldAutoOpenPortalTourPanel", () => {
  it("nunca abre o painel automaticamente", () => {
    assert.equal(shouldAutoOpenPortalTourPanel(null, CATALOG), false);
    assert.equal(
      shouldAutoOpenPortalTourPanel(progress({ status: "exploring" }), CATALOG),
      false,
    );
    assert.equal(
      shouldAutoOpenPortalTourPanel(
        progress({ status: "completed", completedQuestIds: [] }),
        { ...CATALOG, newQuestIds: ["open-apps"] },
      ),
      false,
    );
  });
});

describe("isPortalTourDismissed", () => {
  it("respeita Agora não na versão atual", () => {
    assert.equal(
      isPortalTourDismissed(progress({ status: "dismissed" }), CATALOG),
      true,
    );
  });

  it("reabre card quando há novidades obrigatórias após bump", () => {
    const remote = progress({
      status: "dismissed",
      tourVersion: "2026-06-portal-v6-explore",
    });
    const catalog = {
      ...CATALOG,
      newQuestIds: ["sidebar-theme"],
    };
    assert.equal(isPortalTourDismissed(remote, catalog), false);
  });
});

describe("shouldActivatePortalTourSession", () => {
  it("não ativa no 1º acesso sem progresso", () => {
    assert.equal(shouldActivatePortalTourSession(null, CATALOG), false);
  });

  it("não ativa quando dismissed", () => {
    assert.equal(
      shouldActivatePortalTourSession(
        progress({ status: "dismissed" }),
        CATALOG,
      ),
      false,
    );
  });

  it("ativa quando exploring com progresso", () => {
    assert.equal(
      shouldActivatePortalTourSession(
        progress({ status: "exploring", completedQuestIds: ["open-apps"] }),
        CATALOG,
      ),
      true,
    );
  });
});

describe("resolvePortalTourHomeEntryState", () => {
  it("esconde o card quando dismissed", () => {
    const entry = resolvePortalTourHomeEntryState(
      "user-1",
      progress({ status: "dismissed", completedQuestIds: ["open-apps"] }),
      CATALOG,
    );
    assert.equal(entry.visible, false);
  });

  it("mostra o card enquanto exploring incompleto", () => {
    const entry = resolvePortalTourHomeEntryState(
      "user-1",
      progress({ status: "exploring", completedQuestIds: ["open-apps"] }),
      CATALOG,
    );
    assert.equal(entry.visible, true);
    assert.equal(entry.requiredDone, 1);
    assert.equal(entry.requiredTotal, 6);
  });
});
