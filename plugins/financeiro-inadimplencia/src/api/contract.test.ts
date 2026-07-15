import { describe, expect, it, vi } from "vitest";

import { unwrapApiDelpiEnvelope } from "../types/api";
import type {
  DelayRangeCode,
  InadimplenciaFaixasData,
  InadimplenciaResumoData,
} from "../types/inadimplencia";

const OFFICIAL_RANGE_ORDER: DelayRangeCode[] = [
  "EM_DIA",
  "ATRASO_1_A_5_DIAS",
  "ATRASO_6_A_15_DIAS",
  "ATRASO_16_A_30_DIAS",
  "ATRASO_ACIMA_30_DIAS",
];

describe("contrato API real (envelope + snake_case)", () => {
  it("aceita envelope { success, data } com campos snake_case do resumo", () => {
    const payload = {
      success: true,
      data: {
        periodo: {
          data_inicio: "2025-07-01",
          data_fim_exclusiva: "2026-07-01",
          rotulo: "Jul/2025 – Jun/2026",
        },
        totais: {
          titulos: 6111,
          titulos_em_dia: 5624,
          titulos_atraso: 487,
          valor_total: 1000.5,
          valor_atraso: 97.1,
        },
        indicadores: {
          percentual_em_dia_qtd: 92.03,
          percentual_inadimplencia_qtd: 7.97,
          percentual_em_dia_valor: 90.29,
          percentual_inadimplencia_valor: 9.71,
        },
      },
    };

    const data = unwrapApiDelpiEnvelope<InadimplenciaResumoData>(payload);
    expect(data.periodo.data_fim_exclusiva).toBe("2026-07-01");
    expect(data.totais.titulos).toBe(6111);
    expect(data.indicadores.percentual_em_dia_qtd).toBeCloseTo(92.03);
    expect(Number.isFinite(data.totais.valor_total)).toBe(true);
  });

  it("mantém ordem oficial das faixas", () => {
    const payload = {
      success: true,
      data: {
        periodo: {
          data_inicio: "2025-07-01",
          data_fim_exclusiva: "2026-07-01",
          rotulo: "x",
        },
        items: OFFICIAL_RANGE_ORDER.map((codigo, index) => ({
          codigo,
          rotulo: codigo,
          ordem: index + 1,
          quantidade: index,
          valor: index * 10,
          percentual_quantidade: index,
          percentual_valor: index,
        })),
      } satisfies InadimplenciaFaixasData,
    };

    const data = unwrapApiDelpiEnvelope<InadimplenciaFaixasData>(payload);
    expect(data.items.map((item) => item.codigo)).toEqual(OFFICIAL_RANGE_ORDER);
  });

  it("rejeita sucesso falso e ausência de data", () => {
    expect(() => unwrapApiDelpiEnvelope({ success: false, error: { message: "x" } })).toThrow(
      /x/,
    );
    expect(() => unwrapApiDelpiEnvelope({ success: true })).toThrow(/sem campo data/);
  });
});

describe("paginação snake_case", () => {
  it("preserva pagination page/page_size/total_items", () => {
    const data = unwrapApiDelpiEnvelope<{
      pagination: {
        page: number;
        page_size: number;
        total_items: number;
        total_pages: number;
        has_next: boolean;
        has_previous: boolean;
      };
      items: Array<{ cliente_codigo: string; valor_atraso: number }>;
    }>({
      success: true,
      data: {
        pagination: {
          page: 1,
          page_size: 20,
          total_items: 40,
          total_pages: 2,
          has_next: true,
          has_previous: false,
        },
        items: [{ cliente_codigo: "0001", valor_atraso: 1234.56 }],
      },
    });

    expect(data.pagination.page_size).toBe(20);
    expect(data.pagination.total_items).toBe(40);
    expect(data.items[0]?.valor_atraso).toBeCloseTo(1234.56);
  });
});

describe("fetch API com envelope", () => {
  it("clientes e títulos usam query snake_case", async () => {
    const fetchMock = vi.fn(async (url: string) => {
      if (url.includes("/clientes")) {
        expect(url).toContain("only_with_delays=true");
        expect(url).toContain("sort_by=late_amount");
        expect(url).toContain("page=1");
        return new Response(
          JSON.stringify({
            success: true,
            data: {
              periodo: { data_inicio: "a", data_fim_exclusiva: "b", rotulo: "r" },
              pagination: {
                page: 1,
                page_size: 20,
                total_items: 1,
                total_pages: 1,
                has_next: false,
                has_previous: false,
              },
              items: [
                {
                  cliente_codigo: "C1",
                  loja: "01",
                  nome_cliente: "ACME",
                  nome_reduzido: "ACME",
                  total_titulos: 2,
                  titulos_em_dia: 1,
                  titulos_atraso: 1,
                  valor_total: 100,
                  valor_atraso: 40,
                  percentual_em_dia_qtd: 50,
                  percentual_em_dia_valor: 60,
                },
              ],
            },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        );
      }

      expect(url).toContain("customer_code=C1");
      expect(url).toContain("store_code=01");
      expect(url).toContain("status=late");
      return new Response(
        JSON.stringify({
          success: true,
          data: {
            periodo: { data_inicio: "a", data_fim_exclusiva: "b", rotulo: "r" },
            pagination: {
              page: 1,
              page_size: 20,
              total_items: 1,
              total_pages: 1,
              has_next: false,
              has_previous: false,
            },
            items: [
              {
                prefixo: "NF",
                numero: "1",
                parcela: "1",
                tipo: "NF",
                data_emissao: "2026-01-01",
                data_vencimento_real: "2026-01-10",
                data_baixa: "2026-02-01",
                valor_titulo: 40,
                dias_atraso: 22,
                faixa_atraso: { codigo: "ATRASO_16_A_30_DIAS", rotulo: "16 a 30" },
              },
            ],
          },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    });

    vi.stubGlobal("fetch", fetchMock);

    const { fetchInadimplenciaClientes, fetchInadimplenciaTitulos } = await import(
      "../api/inadimplenciaApi"
    );

    const clientes = await fetchInadimplenciaClientes({
      page: 1,
      pageSize: 20,
      onlyWithDelays: true,
      sortBy: "late_amount",
      sortDir: "desc",
    });
    expect(clientes.items[0]?.nome_cliente).toBe("ACME");

    const titulos = await fetchInadimplenciaTitulos({
      customerCode: "C1",
      storeCode: "01",
      status: "late",
      page: 1,
      pageSize: 20,
    });
    expect(titulos.items[0]?.dias_atraso).toBe(22);
    expect(titulos.pagination.total_items).toBe(1);

    vi.unstubAllGlobals();
  });
});
