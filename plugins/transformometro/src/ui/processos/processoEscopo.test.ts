import { describe, expect, it } from "vitest";

import type { Processo } from "../../data/api/transformometroApi";
import {
  formatInstanciaSetoresDisplay,
  formatInstanciaUnidadeDisplay,
  formatProcessoEscopoRead,
} from "./processoEscopo";

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
