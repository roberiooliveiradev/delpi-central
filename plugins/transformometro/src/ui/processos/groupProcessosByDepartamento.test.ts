import { describe, expect, it } from "vitest";

import type { Processo } from "../../data/api/transformometroApi";
import {
  groupProcessosByDepartamento,
  resolveProcessoDepartamentos,
  SEM_DEPARTAMENTO_KEY,
  sortDepartamentoFolders,
} from "./groupProcessosByDepartamento";

function processo(
  partial: Partial<Processo> & Pick<Processo, "processo_id" | "codigo_processo" | "nome_processo">,
): Processo {
  return {
    status_processo: "ativo",
    ...partial,
  } as Processo;
}

describe("groupProcessosByDepartamento", () => {
  it("resolve setores enriquecidos do escopo", () => {
    const refs = resolveProcessoDepartamentos(
      processo({
        processo_id: "p1",
        codigo_processo: "PROC-1",
        nome_processo: "Alpha",
        setores: [
          { setor_id: "eng", codigo_setor: "engenharia", nome_setor: "Engenharia" },
          { setor_id: "qual", codigo_setor: "qualidade", nome_setor: "Qualidade" },
        ],
      }),
    );
    expect(refs.map((r) => r.key)).toEqual(["engenharia", "qualidade"]);
  });

  it("coloca o mesmo processo em várias pastas (N:N)", () => {
    const shared = processo({
      processo_id: "p-multi",
      codigo_processo: "PROC-9",
      nome_processo: "Multi",
      setores: [
        { setor_id: "a", codigo_setor: "a", nome_setor: "A" },
        { setor_id: "b", codigo_setor: "b", nome_setor: "B" },
      ],
    });
    const folders = groupProcessosByDepartamento([shared]);
    expect(folders).toHaveLength(2);
    expect(folders.every((f) => f.processes.some((p) => p.processo_id === "p-multi"))).toBe(true);
  });

  it("agrupa processos sem departamento", () => {
    const folders = groupProcessosByDepartamento([
      processo({ processo_id: "p0", codigo_processo: "PROC-0", nome_processo: "Orfão" }),
    ]);
    expect(folders).toHaveLength(1);
    expect(folders[0].key).toBe(SEM_DEPARTAMENTO_KEY);
    expect(folders[0].label).toBe("Sem departamento");
  });

  it("mantém «Sem departamento» no fim ao ordenar", () => {
    const folders = sortDepartamentoFolders(
      [
        {
          key: SEM_DEPARTAMENTO_KEY,
          label: "Sem departamento",
          codigoSetor: "",
          processes: [],
          processCount: 0,
        },
        {
          key: "z",
          label: "Zebra",
          codigoSetor: "z",
          processes: [],
          processCount: 0,
        },
        {
          key: "a",
          label: "Alpha",
          codigoSetor: "a",
          processes: [],
          processCount: 0,
        },
      ],
      "asc",
    );
    expect(folders.map((f) => f.key)).toEqual(["a", "z", SEM_DEPARTAMENTO_KEY]);
  });
});
