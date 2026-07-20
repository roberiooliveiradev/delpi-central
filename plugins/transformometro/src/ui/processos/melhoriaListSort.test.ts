import { describe, expect, it } from "vitest";

import type { ProcessoInstancia } from "../../data/api/transformometroApi";
import {
  melhoriaFolderTitle,
  sortMelhoriaListItems,
  type MelhoriaListSort,
} from "./melhoriaListSort";

function row(partial: Partial<ProcessoInstancia>): ProcessoInstancia {
  return {
    instancia_id: partial.instancia_id ?? "i1",
    processo_id: "p1",
    rotulo_instancia: partial.rotulo_instancia,
    codigo_filial: partial.codigo_filial ?? "01",
    nome_filial: partial.nome_filial ?? "Santa Catarina",
    status_instancia: partial.status_instancia ?? "ativo",
    fase_melhoria: partial.fase_melhoria ?? "planejado",
    prioridade: partial.prioridade ?? "media",
    todas_filiais_ativas: partial.todas_filiais_ativas ?? false,
    ...partial,
  } as ProcessoInstancia;
}

describe("melhoriaListSort", () => {
  it("usa rótulo como título da pasta", () => {
    expect(melhoriaFolderTitle(row({ rotulo_instancia: "Automação" }), 2)).toBe("Automação");
  });

  it("ordena por título ascendente", () => {
    const items = [
      row({ instancia_id: "b", rotulo_instancia: "Beta" }),
      row({ instancia_id: "a", rotulo_instancia: "Alfa" }),
    ];
    const sort: MelhoriaListSort = { key: "titulo", direction: "asc" };
    const sorted = sortMelhoriaListItems(items, sort, 1);
    expect(sorted.map((item) => item.instancia_id)).toEqual(["a", "b"]);
  });
});
