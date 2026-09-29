import { describe, expect, it } from "vitest";

import type { TransformometroEntityUpdatedEvent } from "../../constants/realtime";
import {
  documentIdFromEvent,
  resolveProcessDocumentEventIntent,
} from "./processDocumentRealtime";

const CLIENT = "tab-1";

function evt(
  overrides: Partial<TransformometroEntityUpdatedEvent> = {},
): TransformometroEntityUpdatedEvent {
  return {
    type: "entity.updated",
    entityType: "process_document",
    entityId: "doc-1",
    action: "update",
    sectionKey: "documentacao",
    actorUserId: "user-2",
    actorClientId: "tab-2",
    payload: { processo_id: "proc-1", document_id: "doc-1" },
    ...overrides,
  };
}

const view = { selectedId: "doc-1", editingDocumentId: null, clientId: CLIENT };
const edit = {
  selectedId: "doc-1",
  editingDocumentId: "doc-1",
  clientId: CLIENT,
};

describe("resolveProcessDocumentEventIntent", () => {
  it("ignora eventos de outras entidades", () => {
    expect(
      resolveProcessDocumentEventIntent(
        evt({ entityType: "processo", action: "update" }),
        view,
      ),
    ).toEqual({ type: "ignore" });
  });

  it("ignora echo da mesma aba (actorClientId === clientId)", () => {
    expect(
      resolveProcessDocumentEventIntent(evt({ actorClientId: CLIENT }), view),
    ).toEqual({ type: "ignore" });
  });

  it("create remoto atualiza só a lista", () => {
    expect(
      resolveProcessDocumentEventIntent(evt({ action: "create" }), view),
    ).toEqual({ type: "refresh-list" });
  });

  it("update remoto em doc não selecionado atualiza só a lista", () => {
    expect(
      resolveProcessDocumentEventIntent(
        evt({ entityId: "doc-9", payload: { document_id: "doc-9" } }),
        view,
      ),
    ).toEqual({ type: "refresh-list" });
  });

  it("update remoto no doc aberto em view recarrega lista + detalhe", () => {
    expect(resolveProcessDocumentEventIntent(evt(), view)).toEqual({
      type: "refresh-list-and-detail",
    });
  });

  it("update remoto no doc em edição preserva o rascunho (stale banner)", () => {
    expect(resolveProcessDocumentEventIntent(evt(), edit)).toEqual({
      type: "stale-draft",
    });
  });

  it("delete remoto do doc aberto em view sinaliza remoção", () => {
    expect(
      resolveProcessDocumentEventIntent(evt({ action: "delete" }), view),
    ).toEqual({ type: "remote-delete", editing: false });
  });

  it("delete remoto do doc em edição preserva rascunho e sinaliza", () => {
    expect(
      resolveProcessDocumentEventIntent(evt({ action: "delete" }), edit),
    ).toEqual({ type: "remote-delete", editing: true });
  });

  it("delete remoto de outro doc atualiza só a lista", () => {
    expect(
      resolveProcessDocumentEventIntent(
        evt({ action: "delete", entityId: "doc-9", payload: { document_id: "doc-9" } }),
        view,
      ),
    ).toEqual({ type: "refresh-list" });
  });

  it("document_id vem do payload com fallback ao entityId", () => {
    expect(
      documentIdFromEvent(evt({ payload: { document_id: "doc-x" } })),
    ).toBe("doc-x");
    expect(documentIdFromEvent(evt({ payload: {} }))).toBe("doc-1");
  });
});
