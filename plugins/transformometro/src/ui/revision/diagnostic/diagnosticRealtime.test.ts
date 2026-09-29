import { describe, expect, it } from "vitest";

import type { TransformometroEntityUpdatedEvent } from "../../../constants/realtime";
import { resolveDiagnosticEventIntent } from "./diagnosticRealtime";

const CTX = {
  selectedId: "diag-1",
  hasLocalMaterialState: false,
  clientId: "client-a",
};

function evt(partial: Partial<TransformometroEntityUpdatedEvent>): TransformometroEntityUpdatedEvent {
  return {
    type: "entity.updated",
    entityType: "diagnostic",
    entityId: "diag-1",
    action: "update",
    sectionKey: "diagnostico",
    payload: { revisao_id: "rev-1" },
    ...partial,
  };
}

describe("resolveDiagnosticEventIntent", () => {
  it("ignora eventos de outros tipos de entidade", () => {
    expect(
      resolveDiagnosticEventIntent(evt({ entityType: "processo" }), CTX),
    ).toEqual({ type: "ignore" });
  });

  it("ignora eco da própria aba (actorClientId igual)", () => {
    expect(
      resolveDiagnosticEventIntent(evt({ actorClientId: "client-a" }), CTX),
    ).toEqual({ type: "ignore" });
  });

  it("create remoto recarrega a lista", () => {
    expect(
      resolveDiagnosticEventIntent(evt({ action: "create", entityId: "diag-9" }), CTX),
    ).toEqual({ type: "refresh-list" });
  });

  it("update no diagnóstico selecionado sem estado local recarrega lista+detail", () => {
    expect(resolveDiagnosticEventIntent(evt({}), CTX)).toEqual({
      type: "refresh-list-and-detail",
    });
  });

  it("update em outro diagnóstico recarrega só a lista", () => {
    expect(
      resolveDiagnosticEventIntent(evt({ entityId: "diag-2" }), CTX),
    ).toEqual({ type: "refresh-list" });
  });

  it("update no selecionado com formulário/proposta abertos gera conflito local (sem auto-merge)", () => {
    expect(
      resolveDiagnosticEventIntent(evt({}), { ...CTX, hasLocalMaterialState: true }),
    ).toEqual({ type: "local-conflict" });
  });

  it("evento desconhecido no selecionado sem estado local recarrega lista", () => {
    expect(
      resolveDiagnosticEventIntent(evt({ action: "custom" }), {
        ...CTX,
        selectedId: "diag-2",
      }),
    ).toEqual({ type: "refresh-list" });
  });
});
