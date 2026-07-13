import { describe, expect, it } from "vitest";

import type { OptionsData, Processo } from "../../data/api/transformometroApi";
import {
  formatInstanciaSetoresDisplay,
  formatInstanciaUnidadeDisplay,
  formatProcessoEscopoRead,
  resolveCreateInstanciaEscopo,
  type ProcessoEscopoState,
} from "./processoEscopo";

const options = {
  filiais: [
    { id: "01", label: "Santa Catarina" },
    { id: "02", label: "Espírito Santo" },
  ],
  setores: [
    { id: "almoxarifado", label: "Almoxarifado", filiais: ["01"] },
    { id: "comercial", label: "Comercial", filiais: ["01", "02"] },
    { id: "qualidade", label: "Qualidade", filiais: ["01", "02"] },
  ],
} as OptionsData;

describe("resolveCreateInstanciaEscopo", () => {
  it("herda escopo do processo quando preferProcesso é true", () => {
    const processoEscopo: ProcessoEscopoState = {
      todas_filiais_ativas: true,
      filial_ids: [],
      setor_ids: ["comercial", "qualidade"],
    };
    const resolved = resolveCreateInstanciaEscopo(options, processoEscopo, true);
    expect(resolved).toEqual({
      todas_filiais_ativas: true,
      filial_ids: [],
      setor_ids: ["comercial", "qualidade"],
      filialId: "01",
    });
  });

  it("usa primeira filial/setor quando não herda do processo", () => {
    const resolved = resolveCreateInstanciaEscopo(options, null, false);
    expect(resolved).toEqual({
      todas_filiais_ativas: false,
      filial_ids: ["01"],
      setor_ids: ["almoxarifado"],
      filialId: "01",
    });
  });
});

describe("processoEscopo display", () => {
  it("formatProcessoEscopoRead omite códigos de unidade e departamento", () => {
    const processo = {
      todas_filiais_ativas: true,
      setores: [
        { setor_id: "1", codigo_setor: "comercial", nome_setor: "Comercial" },
        { setor_id: "2", codigo_setor: "rh", nome_setor: "Recursos Humanos" },
      ],
    } as Processo;

    const read = formatProcessoEscopoRead(processo, 2);

    expect(read.unidades).toBe("Todas as unidades ativas (2 unidades ativas)");
    expect(read.departamentos).toBe("Comercial; Recursos Humanos");
    expect(read.departamentos).not.toContain("comercial");
    expect(read.departamentos).not.toContain("rh");
  });

  it("formatInstanciaUnidadeDisplay usa nome da filial", () => {
    expect(
      formatInstanciaUnidadeDisplay({
        codigo_filial: "01",
        nome_filial: "Santa Catarina",
      })
    ).toBe("Santa Catarina");
  });

  it("formatInstanciaSetoresDisplay usa nomes dos departamentos", () => {
    expect(
      formatInstanciaSetoresDisplay({
        setores: [
          { setor_id: "1", codigo_setor: "qualidade", nome_setor: "Qualidade" },
        ],
      })
    ).toBe("Qualidade");
  });
});
