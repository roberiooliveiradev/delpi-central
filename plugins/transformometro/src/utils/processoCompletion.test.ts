import { describe, expect, it } from "vitest";

import type { Processo } from "../data/api/transformometroApi";
import {
  computeProcessoListCompletion,
  computeProcessoSetupCompletion,
} from "./processoCompletion";

const baseProcesso: Processo = {
  processo_id: "p1",
  codigo_processo: "PROC-0033",
  nome_processo: "Coleta de documentação",
  filial_id: "01",
  setor_id: "ENG",
  status_processo: "ativo",
  descricao_processo: "Coleta da documentação necessária",
};

describe("computeProcessoSetupCompletion", () => {
  it("usa checklist de 10 itens no detalhe", () => {
    const result = computeProcessoSetupCompletion({
      processo: baseProcesso,
      instanciaCount: 0,
      diagramNodeCount: 0,
      decompositionNodeCount: 0,
      revisoes: [],
    });
    expect(result.total).toBe(10);
    expect(result.done).toBe(1);
    expect(result.percent).toBe(10);
  });
});

describe("computeProcessoListCompletion", () => {
  it("alinha listagem com o mesmo checklist do detalhe", () => {
    const list = computeProcessoListCompletion({
      ...baseProcesso,
      setup_stats: {
        instancia_count: 0,
        diagram_node_count: 0,
        decomposition_node_count: 0,
        has_baseline: false,
        has_melhoria: false,
        has_medicao: false,
      },
    });
    const detail = computeProcessoSetupCompletion({
      processo: baseProcesso,
      instanciaCount: 0,
      diagramNodeCount: 0,
      decompositionNodeCount: 0,
      revisoes: [],
    });
    expect(list.percent).toBe(detail.percent);
    expect(list.done).toBe(detail.done);
    expect(list.total).toBe(detail.total);
  });

  it("marca melhorias e baseline quando setup_stats indica", () => {
    const result = computeProcessoListCompletion({
      ...baseProcesso,
      setup_stats: {
        instancia_count: 2,
        diagram_node_count: 3,
        decomposition_node_count: 5,
        has_baseline: true,
        has_melhoria: true,
        has_medicao: true,
      },
    });
    expect(result.done).toBe(7);
    expect(result.percent).toBe(70);
  });
});
