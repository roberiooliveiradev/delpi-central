import { describe, expect, it } from "vitest";

import { emptyProcessoForm, masterPayloadFromProcessoForm } from "./processoForm";
import {
  defaultProcessoEscopoForCreate,
  emptyProcessoEscopo,
  hasProcessoEscopo,
} from "./processoEscopo";

describe("processoEscopo", () => {
  it("escopo vazio não é considerado configurado", () => {
    expect(hasProcessoEscopo(emptyProcessoEscopo())).toBe(false);
  });

  it("escopo exige ao menos um departamento", () => {
    expect(
      hasProcessoEscopo({
        todas_filiais_ativas: false,
        filial_ids: ["01"],
        setor_ids: [],
      })
    ).toBe(false);
    expect(
      hasProcessoEscopo({
        todas_filiais_ativas: false,
        filial_ids: ["01"],
        setor_ids: ["engenharia"],
      })
    ).toBe(true);
  });
  it("defaultProcessoEscopoForCreate pré-seleciona unidade e departamento", () => {
    const escopo = defaultProcessoEscopoForCreate({
      filiais: [{ id: "01", label: "SC" }],
      setores: [{ id: "engenharia", label: "Engenharia", filiais: ["01"] }],
      status_processo: [],
    } as never);

    expect(hasProcessoEscopo(escopo)).toBe(true);
    expect(escopo.filial_ids).toEqual(["01"]);
    expect(escopo.setor_ids).toEqual(["engenharia"]);
  });
});

describe("masterPayloadFromProcessoForm", () => {
  it("não envia escopo quando departamentos não estão definidos", () => {
    const form = emptyProcessoForm();
    form.nome_processo = "Indicadores Estratégicos";

    const payload = masterPayloadFromProcessoForm(form);

    expect(payload.nome_processo).toBe("Indicadores Estratégicos");
    expect(payload.filial_ids).toBeUndefined();
    expect(payload.setor_ids).toBeUndefined();
    expect(payload.todas_filiais_ativas).toBeUndefined();
  });

  it("inclui escopo quando departamentos estão definidos", () => {
    const form = emptyProcessoForm();
    form.escopo = {
      todas_filiais_ativas: false,
      filial_ids: ["01"],
      setor_ids: ["engenharia"],
    };

    const payload = masterPayloadFromProcessoForm(form);

    expect(payload.filial_ids).toEqual(["01"]);
    expect(payload.setor_ids).toEqual(["engenharia"]);
  });
});
