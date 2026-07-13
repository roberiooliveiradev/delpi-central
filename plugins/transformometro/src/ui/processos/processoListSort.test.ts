import { beforeEach, describe, expect, it, vi } from "vitest";

import type { Processo } from "../../data/api/transformometroApi";
import {
  DEFAULT_PROCESSO_LIST_SORT,
  readProcessoListSort,
  sortProcessoListItems,
  writeProcessoListSort,
} from "./processoListSort";
import { fieldVisibilityForProcessoListView } from "./processoListViewMode";

function processo(partial: Partial<Processo> & Pick<Processo, "processo_id" | "codigo_processo" | "nome_processo">): Processo {
  return {
    status_processo: "ativo",
    ...partial,
  } as Processo;
}

describe("processoListSort", () => {
  beforeEach(() => {
    const storage = new Map<string, string>();
    vi.stubGlobal("localStorage", {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => {
        storage.set(key, value);
      },
      removeItem: (key: string) => {
        storage.delete(key);
      },
      clear: () => {
        storage.clear();
      },
      key: () => null,
      length: 0,
    });
  });

  it("ordena por título ascendente por padrão", () => {
    const items = [
      processo({ processo_id: "1", codigo_processo: "PROC-0002", nome_processo: "Beta" }),
      processo({ processo_id: "2", codigo_processo: "PROC-0001", nome_processo: "Alfa" }),
    ];
    const sorted = sortProcessoListItems(items, DEFAULT_PROCESSO_LIST_SORT);
    expect(sorted.map((row) => row.nome_processo)).toEqual(["Alfa", "Beta"]);
  });

  it("inverte ordem quando direction é desc", () => {
    const items = [
      processo({ processo_id: "1", codigo_processo: "PROC-0001", nome_processo: "Alfa" }),
      processo({ processo_id: "2", codigo_processo: "PROC-0002", nome_processo: "Beta" }),
    ];
    const sorted = sortProcessoListItems(items, { key: "nome", direction: "desc" });
    expect(sorted.map((row) => row.nome_processo)).toEqual(["Beta", "Alfa"]);
  });

  it("persiste sort no localStorage", () => {
    writeProcessoListSort({ key: "codigo", direction: "desc" });
    expect(readProcessoListSort()).toEqual({ key: "codigo", direction: "desc" });
  });

  it("ordena por data de atualização", () => {
    const items = [
      processo({
        processo_id: "1",
        codigo_processo: "PROC-0001",
        nome_processo: "Antigo",
        updated_at: "2026-01-01T10:00:00Z",
      }),
      processo({
        processo_id: "2",
        codigo_processo: "PROC-0002",
        nome_processo: "Recente",
        updated_at: "2026-07-01T10:00:00Z",
      }),
      processo({
        processo_id: "3",
        codigo_processo: "PROC-0003",
        nome_processo: "Sem data",
      }),
    ];
    const asc = sortProcessoListItems(items, { key: "atualizado", direction: "asc" });
    expect(asc.map((row) => row.nome_processo)).toEqual(["Sem data", "Antigo", "Recente"]);
    const desc = sortProcessoListItems(items, { key: "atualizado", direction: "desc" });
    expect(desc.map((row) => row.nome_processo)).toEqual(["Recente", "Antigo", "Sem data"]);
  });
});

describe("fieldVisibilityForProcessoListView", () => {
  it("modo grandes mostra só título", () => {
    expect(fieldVisibilityForProcessoListView("icons-lg")).toEqual({
      showCode: false,
      showMeta: false,
      showStatus: false,
      showProgress: false,
    });
  });

  it("modo médios adiciona código e meta", () => {
    expect(fieldVisibilityForProcessoListView("icons-md")).toEqual({
      showCode: true,
      showMeta: true,
      showStatus: false,
      showProgress: false,
    });
  });

  it("modo lista inclui status e preenchimento", () => {
    expect(fieldVisibilityForProcessoListView("list")).toEqual({
      showCode: true,
      showMeta: true,
      showStatus: true,
      showProgress: true,
    });
  });
});
