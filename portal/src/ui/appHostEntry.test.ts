import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { toFederatedAppRouteProps } from "./appHostEntry.ts";

describe("toFederatedAppRouteProps", () => {
  it("extrai path, entry e openInNewTab para o MFE", () => {
    assert.deepEqual(
      toFederatedAppRouteProps([
        {
          app: "maintenance",
          path: "/apps/maintenance/filial-01/manutencao-geral",
          entry: "https://script.google.com/macros/s/ABC/exec",
          openInNewTab: true,
          showInMenu: false,
        },
        {
          app: "maintenance",
          path: "/apps/maintenance",
          showInMenu: true,
        },
      ]),
      [
        {
          path: "/apps/maintenance/filial-01/manutencao-geral",
          entry: "https://script.google.com/macros/s/ABC/exec",
          openInNewTab: true,
        },
        {
          path: "/apps/maintenance",
          entry: null,
          openInNewTab: false,
        },
      ],
    );
  });

  it("retorna lista vazia sem rotas", () => {
    assert.deepEqual(toFederatedAppRouteProps(undefined), []);
    assert.deepEqual(toFederatedAppRouteProps([]), []);
  });
});
