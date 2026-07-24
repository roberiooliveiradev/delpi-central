import { describe, expect, it } from "vitest";

import { resolveCollaborativeEntityUpdate } from "./collaborativeEntityUpdate";

describe("resolveCollaborativeEntityUpdate", () => {
  it("ignora evento da mesma aba (clientId)", () => {
    expect(
      resolveCollaborativeEntityUpdate({
        editingSectionKey: null,
        actorClientId: "c1",
        myClientId: "c1",
        actorUserId: "u1",
        myUserId: "u1",
      })
    ).toEqual({ kind: "ignore_own" });
  });

  it("não ignora só por mesmo userId (multi-aba sincroniza)", () => {
    expect(
      resolveCollaborativeEntityUpdate({
        editingSectionKey: null,
        updatedSectionKey: "medicao",
        updatedSectionLabel: "Medição",
        actorUserId: "u1",
        myUserId: "u1",
        actorClientId: "aba-a",
        myClientId: "aba-b",
      })
    ).toEqual({
      kind: "resync",
      notice: "Medição atualizado por outro usuário.",
    });
  });

  it("legado sem clientId: não ignora por userId", () => {
    expect(
      resolveCollaborativeEntityUpdate({
        editingSectionKey: null,
        actorUserId: "u1",
        myUserId: "u1",
      }).kind
    ).toBe("resync");
  });

  it("recarrega quando ninguém está editando", () => {
    expect(
      resolveCollaborativeEntityUpdate({
        editingSectionKey: null,
        updatedSectionKey: "diagrama_macro",
        updatedSectionLabel: "Diagrama macro",
        actorUserId: "u2",
        myUserId: "u1",
        actorClientId: "c2",
        myClientId: "c1",
      })
    ).toEqual({
      kind: "resync",
      notice: "Diagrama macro atualizado por outro usuário.",
    });
  });

  it("bloqueia recarga ao editar a mesma seção alterada", () => {
    const result = resolveCollaborativeEntityUpdate({
      editingSectionKey: "diagrama_macro",
      updatedSectionKey: "diagrama_macro",
      actorUserId: "u2",
      myUserId: "u1",
      actorClientId: "c2",
      myClientId: "c1",
    });

    expect(result.kind).toBe("block_editing_conflict");
  });

  it("recarrega outras seções enquanto edita uma seção diferente", () => {
    expect(
      resolveCollaborativeEntityUpdate({
        editingSectionKey: "processo",
        updatedSectionKey: "diagrama_macro",
        updatedSectionLabel: "Diagrama macro",
        actorUserId: "u2",
        myUserId: "u1",
        actorClientId: "c2",
        myClientId: "c1",
      })
    ).toEqual({
      kind: "resync",
      notice: "Outro usuário atualizou Diagrama macro. Os demais dados foram recarregados.",
    });
  });
});
