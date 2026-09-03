#!/usr/bin/env node
/**
 * Testes: opTimeline + alocação rica + mapper histórico OV.
 */
import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { allocateOpsToOrders, buildOpsProductIndex } from "./opAllocation.ts";
import { buildOpHorizontalTimeline, buildOpTimelineEvents } from "./opTimeline.ts";
import { mapProposalHistoryToTimelineItems } from "./proposalHistoryFormatting.ts";

describe("opAllocation — campos ricos", () => {
  it("propaga produzido/planejado/emissão/início/armazém na alocação", () => {
    const opsIndex = buildOpsProductIndex({
      items: [
        {
          filial: "01",
          numero_op: "OP001",
          produto: "90AAAA",
          descricao_produto: "Produto A",
          tipo_produto: "PA",
          quantidade_op: 100,
          quantidade_produzida: 40,
          saldo_op: 60,
          data_emissao_op: "2026-01-10",
          data_inicio_prevista_op: "2026-01-15",
          data_fim_prevista_op: "2026-02-01",
          armazem: "01",
          observacao_op: "obs",
        },
      ],
      resumo: [],
    });

    const [line] = allocateOpsToOrders(
      [
        {
          nome_cliente: "ACME",
          tipo_entidade: "CLIENTE",
          tipo_pedido: "N",
          pedido_cliente: "",
          filial: "01",
          pedido: "000123",
          linha: "01",
          produto: "90AAAA",
          codigo_cliente: "",
          codigo_cadastro: "C001",
          loja_cadastro: "01",
          quantidade: 50,
          entregue: 0,
          saldo: 50,
          data_despacho: null,
          data_entrega: "2026-02-10",
          no_estoque: 0,
          estoque_alocado: 0,
          preco_venda: 10,
          valor_aberto: 500,
        },
      ],
      opsIndex,
    );

    const op = line.previsao_op?.opsUtilizadas[0];
    assert.ok(op);
    assert.equal(op.quantidade_op, 100);
    assert.equal(op.quantidade_produzida, 40);
    assert.equal(op.data_emissao_op, "2026-01-10");
    assert.equal(op.data_inicio_prevista_op, "2026-01-15");
    assert.equal(op.armazem, "01");
    assert.equal(op.descricao_produto, "Produto A");
  });
});

describe("buildOpTimelineEvents", () => {
  const baseOp = {
    numero_op: "OP001",
    saldo_op_total: 10,
    saldo_alocado: 5,
    data_fim_prevista_op: "2026-02-01",
    observacao_op: "",
    quantidade_op: 10,
    quantidade_produzida: 2,
    data_emissao_op: "2026-01-10",
    data_inicio_prevista_op: "2026-01-15",
    armazem: "01",
    descricao_produto: "",
  };

  it("omite eventos sem data e inclui marcos com data", () => {
    const items = buildOpTimelineEvents({
      op: { ...baseOp, data_inicio_prevista_op: null },
      orderDeliveryDate: "2026-01-25",
    });
    const titles = items.map((item) => item.title);
    assert.ok(titles.includes("Emissão da OP"));
    assert.ok(!titles.includes("Início previsto"));
    assert.ok(titles.includes("Data de entrega"));
    assert.ok(titles.includes("Fim previsto da OP"));
  });

  it("agrega múltiplos apontamentos em um evento", () => {
    const items = buildOpTimelineEvents({
      op: baseOp,
      appointments: [
        { appointment_date: "2026-01-20", work_center: "CT1" },
        { appointment_date: "2026-01-22", work_center: "CT2" },
      ],
    });
    assert.ok(items.some((item) => String(item.title).includes("2 apontamentos")));
  });

  it("usa fim real do by-op quando presente", () => {
    const items = buildOpTimelineEvents({
      op: baseOp,
      byOp: {
        order: {
          finish_date: "2026-02-05",
          issue_date: "2026-01-09",
        },
      },
    });
    assert.ok(items.some((item) => item.title === "Fim real"));
    const emission = items.find((item) => item.title === "Emissão da OP");
    assert.equal(emission?.occurredAt, "2026-01-09");
  });

  it("monta timeline horizontal com Hoje e ponto atual", () => {
    const events = buildOpTimelineEvents({
      op: baseOp,
      orderDeliveryDate: "2026-01-25",
    });
    const points = buildOpHorizontalTimeline(events);
    assert.ok(points.some((point) => point.kind === "today"));
    assert.equal(points.filter((point) => point.isCurrent).length, 1);
    assert.ok(points.every((point) => point.dateIso));
  });
});

describe("mapProposalHistoryToTimelineItems", () => {
  it("mapeia eventos AIJ para timeline com badges", () => {
    const items = mapProposalHistoryToTimelineItems([
      {
        revision: "01",
        process_code: "10",
        stage_code: "20",
        process_label: "Comercial",
        stage_label: "Em análise",
        start_date: "2026-01-01",
        is_open: true,
        is_current: true,
      },
    ]);
    assert.equal(items.length, 1);
    assert.equal(items[0].title, "Em análise");
    assert.match(String(items[0].detail), /Atual/);
    assert.match(String(items[0].detail), /Em andamento/);
  });
});
