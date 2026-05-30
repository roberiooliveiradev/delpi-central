import { describe, expect, it } from "vitest";

import {
  clearSessionStreamUi,
  getSessionStreamUi,
  patchSessionStreamUi,
} from "./sessionStreamUiCache";

describe("sessionStreamUiCache", () => {
  it("mantém snapshot por sessão enquanto o turno está ativo", () => {
    clearSessionStreamUi("session-a");

    patchSessionStreamUi("session-a", {
      activityLog: [
        {
          id: "web-search",
          message: "Buscando «python» na internet pública",
          state: "active",
        },
      ],
      status: "Buscando «python» na internet pública",
    });

    patchSessionStreamUi("session-b", {
      status: "Outra conversa",
    });

    expect(getSessionStreamUi("session-a").activityLog).toHaveLength(1);
    expect(getSessionStreamUi("session-b").status).toBe("Outra conversa");

    clearSessionStreamUi("session-a");
    expect(getSessionStreamUi("session-a").activityLog).toHaveLength(0);
  });
});
