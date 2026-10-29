/**
 * Relatórios e divergências — terceira aba do Fechamento mensal,
 * versão V0.3 (UX-011, Plano 113 §26, doc 112 §46).
 *
 * Decisões PO congeladas: prioridade=attention (divergências/ações
 * antes do catálogo), catálogo=cards compactos por família, detalhe
 * completo em PÁGINA CONTEXTUAL do relatório (supersede o `inline`
 * da V0.2 — rota `closing/monthly-closing/{period}/reports/{key}`),
 * PDF contextual na página do relatório. Sem quarta aba.
 *
 * Contratos canônicos consumidos (todos via BFF `controllership-
 * finance-api`; nenhum cálculo financeiro no navegador):
 * - `GET /closing/financial-settlements/summary` — grupos R01/R02
 *   (SE5) com totais calculados + quality flags reais;
 * - `GET /closing/stock-inventory` — posição P7 (R03/SB9) com
 *   `status`, totais e agrupamentos;
 * - `GET /closing/competences/{period}/p3` — conciliação canônica
 *   `divergence = reported - expected` por domínio;
 * - `GET /closing/competences/{period}/reports` — cobertura R01–R15.
 *
 * Regras honestas: fonte indisponível/erro não é «zero divergências»;
 * `—` quando não há informação confiável; competência não aberta vira
 * «conferência não realizada» (P3/matriz 404); resultados são keyed
 * por período — dados de um mês nunca aparecem sob outro.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { ApiError } from "../../api/httpClient";
import {
  getFinancialSettlementsSummary,
  type SettlementsSummaryPayload,
} from "../../api/financialSettlementsApi";
import {
  getStockInventory,
  type StockInventoryPayload,
} from "../../api/stockInventoryApi";
import {
  getStockReconciliation,
  type StockReconciliationPayload,
} from "../../api/stockReconciliationApi";
import {
  getP3State,
  type P3Status,
  type ReconciliationDomain,
  type SourceState,
} from "../../api/p3Api";
import {
  listReportMatrix,
  type ReportMatrix,
} from "../../api/reportsApi";
import {
  COVERAGE_LABELS,
  COVERAGE_VARIANTS,
  SOURCE_LABELS,
} from "./ReportsMatrixPanel";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  CfActionButton,
  CfEmptyState,
  CfInteractiveDataCard,
  CfSectionCard,
  CfStatusBadge,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { CF_HELP } from "../../content/helpTooltips";
import {
  formatAmount,
  formatDateTime,
} from "../../utils/formatters";
import {
  REPORT_KEY_TO_FAMILY,
  type ReportFamily,
  type ReportKey,
} from "./MonthlyReportPage";
import {
  AnalyticalReconciliationSection,
  OPERAND_STATUS_LABELS,
} from "./ReportSharedSections";

export type { ReportFamily };

type PanelError = { status: number; code: string | null; message: string };

const ERROR_MESSAGES: Record<string, string> = {
  forbidden: "Você não tem autorização para esta consulta.",
  unauthorized: "Sessão expirada — autentique-se novamente.",
  competence_not_opened: "Competência não aberta.",
  competence_not_found: "Competência não encontrada.",
  not_found: "Competência não encontrada.",
};

const NOT_OPENED_CODES = new Set([
  "competence_not_opened",
  "competence_not_found",
]);

function mapError(error: unknown): PanelError {
  if (error instanceof ApiError) {
    return {
      status: error.status,
      code: error.code ?? null,
      message: ERROR_MESSAGES[error.code ?? ""] ?? error.message,
    };
  }
  return {
    status: 0,
    code: null,
    message: "Falha de comunicação com a API.",
  };
}

function isNotOpened(error: PanelError): boolean {
  return (
    (error.code !== null && NOT_OPENED_CODES.has(error.code)) ||
    error.status === 404
  );
}

// -- fontes ------------------------------------------------------------------

type Source<T> =
  | { kind: "ready"; data: T; at: Date }
  | { kind: "not_opened" }
  | { kind: "error"; error: PanelError };

type Keyed<T> = { key: string; result: Source<T> };

/** Metadados do catálogo — um cartão por relatório implementado. */
const REPORT_META: Record<
  ReportKey,
  { name: string; description: string; origin: string }
> = {
  "financial-settlements": {
    name: "Baixas financeiras",
    description:
      "Pagamentos e recebimentos do período, agrupados por natureza e tipo de movimento.",
    origin: "TOTVS/SE5 — consulta operacional",
  },
  "stock-inventory": {
    name: "Estoque histórico — P7",
    description:
      "Posição de estoque do fechamento (EM ESTOQUE + EM PROCESSO) pelo motor P7.",
    origin: "TOTVS/SB9 + MATR989 — consulta operacional",
  },
  "stock-movements": {
    name: "Entradas e saídas — R05",
    description:
      "Movimentações do mês por tipo de produto e saldo do fechamento — regra MATR320.",
    origin: "TOTVS/SD1·SD2·SD3·SF4 + SB9",
  },
  "work-in-process": {
    name: "Material em processo — R08",
    description:
      "Material em processo físico (armazém 99) e alocado em ordens vivas — regra MATR989.",
    origin: "TOTVS/SB9 + SD3/SC2",
  },
};

const CATALOG_REPORT_KEYS: ReportKey[] = [
  "financial-settlements",
  "stock-inventory",
  "stock-movements",
  "work-in-process",
];

const DOMAIN_LABELS: Record<ReconciliationDomain, string> = {
  ENTRADAS_SAIDAS: "Entradas e saídas (R05)",
  P7: "Posição de estoque P7 (R03)",
  H02: "Posição H02 (R08)",
};

const DOMAIN_OPERAND_LABELS: Record<string, string> = {
  entradasSaidas: "Entradas e saídas (R05)",
  p7: "Posição de estoque P7 (R03)",
  h02: "Material em processo (R08)",
};

/** Domínio P3 → operando da conciliação analítica que o reflete. */
const DOMAIN_TO_OPERAND: Record<
  ReconciliationDomain,
  "entradasSaidas" | "p7" | "h02"
> = {
  ENTRADAS_SAIDAS: "entradasSaidas",
  P7: "p7",
  H02: "h02",
};

const SOURCE_STATE_LABELS: Record<SourceState, string> = {
  AVAILABLE: "Disponível",
  STALE: "Desatualizada",
  UNAVAILABLE: "Indisponível",
  PARTIAL: "Parcial",
  ERROR: "Erro na fonte",
};

const STOCK_STATUS_LABELS: Record<string, string> = {
  available: "Disponível",
  incomplete: "Parcialmente disponível",
  source_missing: "Posição histórica indisponível",
  no_matching_items: "Sem dados para o filtro",
};

function periodRange(period: string): {
  startDate: string;
  endDate: string;
} {
  const [year, month] = period.split("-").map(Number);
  const lastDay = new Date(year, month, 0).getDate();
  return {
    startDate: `${period}-01`,
    endDate: `${period}-${String(lastDay).padStart(2, "0")}`,
  };
}

function formatPeriod(period: string): string {
  const [year, month] = period.split("-");
  return `${month}/${year}`;
}

// -- itens de atenção ---------------------------------------------------------

type AttentionKind =
  | "divergence"
  | "source_unavailable"
  | "check_pending";

type AttentionItem = {
  id: string;
  kind: AttentionKind;
  /** Relatório ou fonte (rótulo humano, nunca código técnico). */
  source: string;
  description: string;
  situation: string;
  /** Valor da diferença quando comprovado pelo backend. */
  difference: string | null;
  /** Rótulo de badge específico — sobrepõe a categoria do `kind`. */
  badgeLabel?: string;
  origin: string;
  fetchedAt: string | null;
  nextAction: string;
  /** Fatos do detalhe expansível (rótulo → valor). */
  facts: [string, string][];
  /** Procedimento homologado de correção manual, quando comprovado. */
  totvsGuide: string | null;
  /** Página contextual relacionada, quando o item pertence a uma família. */
  reportKey?: ReportKey;
};

const KIND_BADGE: Record<
  AttentionKind,
  { label: string; variant: "danger" | "warning" | "info" }
> = {
  divergence: { label: "Divergência comprovada", variant: "danger" },
  source_unavailable: {
    label: "Fonte indisponível",
    variant: "warning",
  },
  check_pending: {
    label: "Conferência não realizada",
    variant: "info",
  },
};

function buildAttentionItems(args: {
  p3: Source<P3Status> | null;
  matrix: Source<ReportMatrix> | null;
  settlements: Source<SettlementsSummaryPayload> | null;
  stock: Source<StockInventoryPayload> | null;
  recon: Source<StockReconciliationPayload> | null;
}): AttentionItem[] {
  const { p3, matrix, settlements, stock, recon } = args;
  const items: AttentionItem[] = [];

  // Conciliação analítica — divergência calculada pela BFF a partir
  // dos três relatórios operacionais (superfície analítica, distinta
  // do workflow governado P3).
  if (recon?.kind === "ready") {
    const data = recon.data;
    if (
      data.eligibility === "ELIGIBLE" &&
      data.parity === "DIVERGENCE" &&
      data.divergenceCents !== null
    ) {
      items.push({
        id: "analytics-divergence",
        kind: "divergence",
        source: "Conciliação analítica de estoque",
        description:
          "Diferença calculada entre Entradas/Saídas, P7 e Material em processo nesta competência.",
        situation: "Divergência identificada",
        difference: formatAmount(data.divergenceCents),
        origin: "Conciliação analítica (E/S − P7 − H02)",
        fetchedAt: recon.at.toISOString(),
        nextAction:
          "Investigue os operandos nos relatórios R05, P7 e R08; a validação formal segue pelo checklist P3.",
        facts: [
          [
            "Entradas e saídas (R05)",
            data.operands.entradasSaidas.value
              ? formatAmount(data.operands.entradasSaidas.value)
              : "—",
          ],
          [
            "Estoque P7 (R03)",
            data.operands.p7.value
              ? formatAmount(data.operands.p7.value)
              : "—",
          ],
          [
            "Material em processo (R08)",
            data.operands.h02.value
              ? formatAmount(data.operands.h02.value)
              : "—",
          ],
          [
            "Divergência",
            formatAmount(data.divergenceCents),
          ],
        ],
        totvsGuide: null,
        reportKey: "stock-inventory",
      });
    } else if (data.eligibility === "INELIGIBLE") {
      const missing = data.ineligibleOperands
        .map(
          (key) =>
            DOMAIN_OPERAND_LABELS[key] ?? key,
        )
        .join(", ");
      const missingDetail = data.ineligibleOperands
        .map((key) => {
          const operand = data.operands[
            key as keyof typeof data.operands
          ];
          const state =
            OPERAND_STATUS_LABELS[operand?.status ?? ""] ?? "—";
          return `${DOMAIN_OPERAND_LABELS[key] ?? key}: ${state}`;
        })
        .join("; ");
      items.push({
        id: "analytics-ineligible",
        kind: "check_pending",
        source: "Conciliação analítica de estoque",
        description: `Operandos indisponíveis ou incompletos: ${missing}. A divergência não é calculada — fonte ausente nunca entra como zero.`,
        situation: "Conciliação pendente",
        difference: null,
        origin: "Conciliação analítica (E/S − P7 − H02)",
        fetchedAt: recon.at.toISOString(),
        nextAction:
          "Consulte os relatórios indisponíveis na origem — a conciliação calcula quando os três operandos estão completos.",
        facts: [
          ["Operandos pendentes", missing],
          ["Detalhe por fonte", missingDetail],
          ["Estado", "Cálculo não realizado"],
        ],
        totvsGuide: null,
      });
    }
  } else if (recon?.kind === "error") {
    items.push({
      id: "analytics-error",
      kind: "source_unavailable",
      source: "Conciliação analítica de estoque",
      description:
        "Não foi possível consultar a conciliação analítica deste período.",
      situation: recon.error.message,
      difference: null,
      origin: "Conciliação analítica (E/S − P7 − H02)",
      fetchedAt: null,
      nextAction: "Atualize a consulta e tente novamente.",
      facts: [["Erro", recon.error.message]],
      totvsGuide: null,
    });
  }

  // Conciliação P3 — divergências monetárias canônicas.
  if (p3?.kind === "ready") {
    for (const recon of p3.data.reconciliations) {
      const label = DOMAIN_LABELS[recon.domain];
      if (recon.source_state !== "AVAILABLE") {
        // `fetched_at` nulo = domínio nunca registrado no workflow
        // governado (default sintetizado pela BFF) — distinguir de uma
        // fonte registrada e marcada indisponível.
        const neverRegistered = !recon.fetched_at;
        // Três dimensões independentes (REWORK-011): a consulta
        // operacional responde por conta própria via operando da
        // conciliação analítica — "consulta disponível" ≠ "elegível
        // p/ conciliar" e "snapshot ausente" ≠ "falha técnica".
        const operandStatus =
          args.recon?.kind === "ready"
            ? (args.recon.data.operands[DOMAIN_TO_OPERAND[recon.domain]]
                .status ?? null)
            : null;
        const operational = operandStatus === "AVAILABLE";
        const snapshotMissing = operandStatus === "SOURCE_MISSING";
        const technicalFailure = operandStatus === "UNAVAILABLE";
        const partialData = operandStatus === "INCOMPLETE";
        const reportKey = DOMAIN_TO_OPERAND[recon.domain] === "entradasSaidas"
          ? ("stock-movements" as const)
          : DOMAIN_TO_OPERAND[recon.domain] === "h02"
            ? ("work-in-process" as const)
            : ("stock-inventory" as const);
        // A dimensão operacional rotula apenas o domínio nunca
        // registrado — a fonte P3 registrada tem estado autoritativo
        // próprio, com a consulta operacional exibida como fato.
        const situation = neverRegistered
          ? operational
            ? "Consulta disponível — conciliação pendente"
            : snapshotMissing
              ? "Posição histórica ainda não disponível"
              : technicalFailure
                ? "Falha ao consultar a fonte"
                : partialData
                  ? "Dados incompletos — conciliação pendente"
                  : "Fonte da conciliação não registrada"
          : SOURCE_STATE_LABELS[recon.source_state];
        const badgeLabel = neverRegistered
          ? operational || partialData
            ? "Conciliação pendente"
            : snapshotMissing
              ? "Sem posição histórica"
              : technicalFailure
                ? "Falha na fonte"
                : "Fonte não registrada"
          : undefined;
        const description = neverRegistered
          ? operational
            ? "O relatório possui dados para análise nesta competência, mas ainda não existe fonte registrada e validada para sua utilização no P3 governado — disponibilidade de consulta não equivale a elegibilidade para conciliar."
            : snapshotMissing
              ? "Não há posição histórica de fechamento disponível para o mês selecionado — a consulta operacional não encontra o snapshot SB9 da data de referência. Isso não é saldo zero nem falha técnica; a fonte P3 também ainda não foi registrada."
              : technicalFailure
                ? "A consulta operacional falhou por erro técnico na origem — a fonte P3 também não está registrada. Nenhum valor é presumido."
                : partialData
                  ? "A consulta operacional responde apenas parcialmente para esta competência — e a fonte P3 ainda não está registrada. Dados incompletos não são apresentados como zero."
                  : "A fonte desta conferência ainda não foi registrada nem validada — a conciliação permanece bloqueada até que exista uma fonte elegível."
          : "A fonte desta conferência não pôde ser consultada ou validada.";
        const nextAction = neverRegistered
          ? operational || partialData
            ? "Abra o relatório para consultar os dados; a elegibilidade da fonte para a conciliação é registrada pela gestão no checklist P3."
            : technicalFailure
              ? "Atualize a consulta e tente novamente — se a falha persistir, verifique a origem no ERP."
              : snapshotMissing
                ? "A posição histórica só existirá após o fechamento de estoque do período no ERP; nenhum dado é presumido."
                : "A conciliação aguarda a validação de uma fonte elegível — consulte o checklist P3 quando a fonte oficial estiver integrada."
          : "Verifique a disponibilidade da fonte no ERP e atualize a consulta.";
        items.push({
          id: `p3-src-${recon.domain}`,
          kind: "source_unavailable",
          source: label,
          description,
          situation,
          badgeLabel,
          difference: null,
          origin: "Conciliação P3",
          fetchedAt: recon.fetched_at,
          nextAction,
          facts: [
            ["Domínio", label],
            [
              "Consulta operacional",
              operational
                ? "Disponível"
                : (OPERAND_STATUS_LABELS[operandStatus ?? ""] ??
                  "—"),
            ],
            [
              "Elegibilidade P3",
              neverRegistered
                ? "Não registrada"
                : SOURCE_STATE_LABELS[recon.source_state],
            ],
            [
              "Última consulta",
              recon.fetched_at
                ? formatDateTime(recon.fetched_at)
                : "—",
            ],
          ],
          totvsGuide: null,
          reportKey,
        });
      } else if (
        recon.divergence !== null &&
        recon.divergence !== "0.00" &&
        recon.divergence !== "0"
      ) {
        items.push({
          id: `p3-div-${recon.domain}`,
          kind: "divergence",
          source: label,
          description:
            "Diferença comprovada entre o valor esperado e o reportado na conciliação.",
          situation: "Divergência comprovada",
          difference: formatAmount(recon.divergence),
          origin: "Conciliação P3",
          fetchedAt: recon.fetched_at,
          nextAction:
            "Confira a origem no TOTVS e revalide a conciliação no checklist P3 após a correção.",
          facts: [
            ["Domínio", label],
            [
              "Valor esperado",
              recon.expected_amount
                ? formatAmount(recon.expected_amount)
                : "—",
            ],
            [
              "Valor reportado",
              recon.reported_amount
                ? formatAmount(recon.reported_amount)
                : "—",
            ],
            [
              "Diferença",
              recon.divergence
                ? formatAmount(recon.divergence)
                : "—",
            ],
            [
              "Última consulta",
              recon.fetched_at
                ? formatDateTime(recon.fetched_at)
                : "—",
            ],
          ],
          totvsGuide:
            "A causa ainda não foi identificada. Confira os lançamentos " +
            "do período no ERP (origem: " +
            label +
            ") e, após o ajuste manual, revalide a conciliação no " +
            "painel P3 do checklist.",
          reportKey: "stock-inventory",
        });
      }
    }
  } else if (p3?.kind === "not_opened") {
    items.push({
      id: "p3-not-opened",
      kind: "check_pending",
      source: "Conciliação de estoque (P3)",
      description:
        "A conferência de estoque ainda não foi executada — a competência precisa estar aberta para a conciliação.",
      situation: "Conferência não realizada",
      difference: null,
      origin: "Conciliação P3",
      fetchedAt: null,
      nextAction:
        "Abra o fechamento do mês e confirme o cutoff P3 para iniciar a conciliação.",
      facts: [
        ["Estado", "Competência não aberta"],
        ["Conferência", "Não executada"],
      ],
      totvsGuide: null,
    });
  } else if (p3?.kind === "error") {
    items.push({
      id: "p3-error",
      kind: "source_unavailable",
      source: "Conciliação de estoque (P3)",
      description:
        "Não foi possível consultar a conciliação de estoque — tente atualizar os dados.",
      situation: p3.error.message,
      difference: null,
      origin: "Conciliação P3",
      fetchedAt: null,
      nextAction: "Atualize a consulta e tente novamente.",
      facts: [["Erro", p3.error.message]],
      totvsGuide: null,
    });
  }

  // Qualidade dos vínculos das baixas — contadores reais do contrato.
  if (settlements?.kind === "ready") {
    const q = settlements.data.quality;
    const findings: [number, string, string][] = [
      [
        q.missingDocumentCount,
        "Baixas sem documento vinculado",
        "baixas sem número de documento",
      ],
      [
        q.missingNatureCount,
        "Baixas sem natureza financeira",
        "baixas sem natureza identificada",
      ],
      [
        q.unresolvedBranchCount,
        "Baixas sem filial identificada",
        "baixas sem filial resolvida",
      ],
    ];
    for (const [count, title, desc] of findings) {
      if (count <= 0) continue;
      items.push({
        id: `set-q-${title}`,
        kind: "divergence",
        source: "Baixas financeiras (SE5)",
        description: `Inconsistência comprovada: ${count} ${desc} no período.`,
        situation: "Inconsistência identificada",
        badgeLabel: "Inconsistência identificada",
        difference: `${count}`,
        origin: "TOTVS/SE5 — qualidade dos vínculos",
        fetchedAt: settlements.at.toISOString(),
        nextAction:
          "Verifique os vínculos no ERP e atualize a consulta após a correção.",
        facts: [
          ["Registros afetados", `${count}`],
          ["Período", formatPeriod(settlements.data.period.start_date.slice(0, 7))],
        ],
        totvsGuide:
          "A causa ainda não foi identificada. Confira o cadastro do " +
          "documento/natureza/filial no ERP e reconsulte os dados.",
        reportKey: "financial-settlements",
      });
    }
  } else if (settlements?.kind === "error") {
    items.push({
      id: "set-error",
      kind: "source_unavailable",
      source: "Baixas financeiras (SE5)",
      description:
        "Não foi possível consultar as baixas financeiras do período.",
      situation: settlements.error.message,
      difference: null,
      origin: "TOTVS/SE5",
      fetchedAt: null,
      nextAction: "Atualize a consulta e tente novamente.",
      facts: [["Erro", settlements.error.message]],
      totvsGuide: null,
      reportKey: "financial-settlements",
    });
  }

  // Posição de estoque — estados de fonte próprios do contrato.
  if (stock?.kind === "ready") {
    if (
      stock.data.status === "source_missing" ||
      stock.data.status === "incomplete"
    ) {
      items.push({
        id: `stock-${stock.data.status}`,
        kind: "source_unavailable",
        source: "Posição de estoque (P7)",
        description:
          stock.data.status === "source_missing"
            ? "O ERP não possui fechamento de estoque registrado para esta competência."
            : "O snapshot de estoque está parcialmente disponível para esta competência.",
        situation: STOCK_STATUS_LABELS[stock.data.status],
        badgeLabel:
          stock.data.status === "source_missing"
            ? "Sem posição histórica"
            : undefined,
        difference: null,
        origin: "TOTVS/SB9",
        fetchedAt: stock.data.dataAsOf,
        nextAction:
          "Consulte outra competência ou filial — a ausência não é um saldo zero.",
        facts: [
          ["Situação", STOCK_STATUS_LABELS[stock.data.status]],
          [
            "Filiais cobertas",
            stock.data.branchesAvailable.length
              ? stock.data.branchesAvailable.join(", ")
              : "—",
          ],
          [
            "Filiais sem snapshot",
            stock.data.branchesMissing.length
              ? stock.data.branchesMissing.join(", ")
              : "—",
          ],
        ],
        totvsGuide: null,
        reportKey: "stock-inventory",
      });
    }
  } else if (stock?.kind === "error") {
    items.push({
      id: "stock-error",
      kind: "source_unavailable",
      source: "Posição de estoque (P7)",
      description:
        "Não foi possível consultar a posição histórica de estoque.",
      situation: stock.error.message,
      difference: null,
      origin: "TOTVS/SB9",
      fetchedAt: null,
      nextAction: "Atualize a consulta e tente novamente.",
      facts: [["Erro", stock.error.message]],
      totvsGuide: null,
      reportKey: "stock-inventory",
    });
  }

  // Cobertura R01–R15 — entregáveis com conferência pendente.
  if (matrix?.kind === "ready") {
    for (const entry of matrix.data.reports) {
      if (entry.checklist_items <= 0 || entry.items_pending <= 0) continue;
      items.push({
        id: `mx-${entry.report_id}`,
        kind: "check_pending",
        source: `${entry.report_id} — ${entry.label}`,
        description: `${entry.items_pending} de ${entry.checklist_items} ` +
          "entregáveis aguardando conferência.",
        situation: "Conferência não realizada",
        difference: null,
        origin: "Matriz de entregáveis do fechamento",
        fetchedAt: null,
        nextAction:
          "Confira as evidências pendentes na aba Documentos e interações.",
        facts: [
          ["Entregáveis", `${entry.checklist_items}`],
          ["Conferidos", `${entry.items_validated}`],
          ["Pendentes", `${entry.items_pending}`],
        ],
        totvsGuide: null,
      });
    }
  } else if (matrix?.kind === "error") {
    items.push({
      id: "mx-error",
      kind: "source_unavailable",
      source: "Matriz de entregáveis (R01–R15)",
      description:
        "Não foi possível consultar a cobertura de entregáveis do fechamento.",
      situation: matrix.error.message,
      difference: null,
      origin: "Checklist da competência",
      fetchedAt: null,
      nextAction: "Atualize a consulta e tente novamente.",
      facts: [["Erro", matrix.error.message]],
      totvsGuide: null,
    });
  }

  const ORDER: Record<AttentionKind, number> = {
    divergence: 0,
    source_unavailable: 1,
    check_pending: 2,
  };
  return items.sort((a, b) => ORDER[a.kind] - ORDER[b.kind]);
}

// -- subcomponentes -----------------------------------------------------------

function AttentionRow({
  item,
  expanded,
  onToggle,
  onOpenReport,
}: {
  item: AttentionItem;
  expanded: boolean;
  onToggle: () => void;
  onOpenReport: (key: ReportKey) => void;
}) {
  const badge = KIND_BADGE[item.kind];
  const detailId = `cf-attn-detail-${item.id}`;
  return (
    <li className="cf-attention-item" data-kind={item.kind}>
      <div className="cf-attention-item__head">
        <div className="cf-attention-item__main">
          <strong>{item.source}</strong>
          <span className="cf-attention-item__desc">
            {item.description}
          </span>
          <span className="cf-attention-item__meta">
            Situação: {item.situation} · Origem: {item.origin}
            {item.fetchedAt
              ? ` · consulta em ${formatDateTime(item.fetchedAt)}`
              : ""}
          </span>
        </div>
        <div className="cf-attention-item__side">
          {item.difference !== null ? (
            <span className="cf-attention-item__value">
              {item.difference}
            </span>
          ) : null}
          <CfStatusBadge
            label={item.badgeLabel ?? badge.label}
            variant={badge.variant}
          />
        </div>
      </div>
      <div className="cf-attention-item__actions">
        <CfActionButton
          variant="ghost"
          aria-expanded={expanded}
          aria-controls={detailId}
          onClick={onToggle}
        >
          {expanded ? "Ocultar detalhes" : "Ver detalhes"}
        </CfActionButton>
        {item.reportKey ? (
          <CfActionButton
            variant="ghost"
            onClick={() => onOpenReport(item.reportKey as ReportKey)}
          >
            Abrir relatório
          </CfActionButton>
        ) : null}
      </div>
      {expanded ? (
        <div className="cf-attention-item__detail" id={detailId}>
          <dl className="cf-attention-facts">
            {item.facts.map(([label, value]) => (
              <div key={label} className="cf-attention-facts__row">
                <dt>{label}</dt>
                <dd>{value}</dd>
              </div>
            ))}
          </dl>
          <p className="cf-attention-item__action">
            <strong>Próxima ação:</strong> {item.nextAction}
          </p>
          {item.totvsGuide ? (
            <p className="cf-attention-item__totvs">
              <strong>Como corrigir no TOTVS:</strong> {item.totvsGuide}
            </p>
          ) : null}
        </div>
      ) : null}
    </li>
  );
}

// -- painel principal ---------------------------------------------------------

export function MonthlyReportsPanel({
  period,
  selectedReport,
  onOpenReport,
}: {
  period: string;
  selectedReport: ReportFamily | null;
  /** Abre a página contextual do relatório (UX-011 D3). */
  onOpenReport: (key: ReportKey) => void;
}) {
  const [nonce, setNonce] = useState(0);
  const reload = useCallback(() => setNonce((n) => n + 1), []);

  const [p3Result, setP3Result] = useState<Keyed<P3Status> | null>(null);
  const [matrixResult, setMatrixResult] =
    useState<Keyed<ReportMatrix> | null>(null);
  const [setResult, setSetResult] =
    useState<Keyed<SettlementsSummaryPayload> | null>(null);
  const [stockResult, setStockResult] =
    useState<Keyed<StockInventoryPayload> | null>(null);
  const [reconResult, setReconResult] =
    useState<Keyed<StockReconciliationPayload> | null>(null);

  const p3Id = useRef(0);
  const matrixId = useRef(0);
  const setId = useRef(0);
  const stockId = useRef(0);
  const reconId = useRef(0);

  const sourceKey = `${period}:${nonce}`;
  const { startDate, endDate } = useMemo(
    () => periodRange(period),
    [period],
  );

  const p3 = p3Result?.key === sourceKey ? p3Result.result : null;
  const matrix =
    matrixResult?.key === sourceKey ? matrixResult.result : null;
  const settlements =
    setResult?.key === sourceKey ? setResult.result : null;
  const stock =
    stockResult?.key === sourceKey ? stockResult.result : null;
  const recon =
    reconResult?.key === sourceKey ? reconResult.result : null;
  const anyLoading =
    p3 === null ||
    matrix === null ||
    settlements === null ||
    stock === null ||
    recon === null;

  useEffect(() => {
    if (!period) return;
    const id = ++p3Id.current;
    const controller = new AbortController();
    getP3State(period, controller.signal)
      .then((data) => {
        if (controller.signal.aborted || p3Id.current !== id) return;
        if (data) {
          setP3Result({
            key: sourceKey,
            result: { kind: "ready", data, at: new Date() },
          });
        } else {
          setP3Result({ key: sourceKey, result: { kind: "not_opened" } });
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || p3Id.current !== id) return;
        const error = mapError(err);
        setP3Result({
          key: sourceKey,
          result: isNotOpened(error)
            ? { kind: "not_opened" }
            : { kind: "error", error },
        });
      });
    return () => controller.abort();
  }, [period, sourceKey]);

  useEffect(() => {
    if (!period) return;
    const id = ++matrixId.current;
    const controller = new AbortController();
    listReportMatrix(period, controller.signal)
      .then((data) => {
        if (controller.signal.aborted || matrixId.current !== id)
          return;
        if (data) {
          setMatrixResult({
            key: sourceKey,
            result: { kind: "ready", data, at: new Date() },
          });
        } else {
          setMatrixResult({
            key: sourceKey,
            result: { kind: "not_opened" },
          });
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || matrixId.current !== id)
          return;
        const error = mapError(err);
        setMatrixResult({
          key: sourceKey,
          result: isNotOpened(error)
            ? { kind: "not_opened" }
            : { kind: "error", error },
        });
      });
    return () => controller.abort();
  }, [period, sourceKey]);

  useEffect(() => {
    if (!period) return;
    const id = ++setId.current;
    const controller = new AbortController();
    getFinancialSettlementsSummary(
      { startDate, endDate },
      { signal: controller.signal },
    )
      .then((data) => {
        if (controller.signal.aborted || setId.current !== id) return;
        setSetResult({
          key: sourceKey,
          result: { kind: "ready", data, at: new Date() },
        });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || setId.current !== id) return;
        setSetResult({
          key: sourceKey,
          result: { kind: "error", error: mapError(err) },
        });
      });
    return () => controller.abort();
  }, [period, sourceKey, startDate, endDate]);

  useEffect(() => {
    if (!period) return;
    const id = ++stockId.current;
    const controller = new AbortController();
    getStockInventory(
      { period, page: 1, pageSize: 25 },
      { signal: controller.signal },
    )
      .then((data) => {
        if (controller.signal.aborted || stockId.current !== id) return;
        setStockResult({
          key: sourceKey,
          result: { kind: "ready", data, at: new Date() },
        });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || stockId.current !== id) return;
        setStockResult({
          key: sourceKey,
          result: { kind: "error", error: mapError(err) },
        });
      });
    return () => controller.abort();
  }, [period, sourceKey]);

  // Conciliação analítica (E/S − P7 − H02) — consulta operacional
  // por mês de referência; não depende de competência aberta nem do
  // fluxo documental (DEC-ANALYTICS-INDEPENDENCE).
  useEffect(() => {
    if (!period) return;
    const id = ++reconId.current;
    const controller = new AbortController();
    getStockReconciliation(
      { period },
      { signal: controller.signal },
    )
      .then((data) => {
        if (controller.signal.aborted || reconId.current !== id) return;
        setReconResult({
          key: sourceKey,
          result: { kind: "ready", data, at: new Date() },
        });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || reconId.current !== id) return;
        setReconResult({
          key: sourceKey,
          result: { kind: "error", error: mapError(err) },
        });
      });
    return () => controller.abort();
  }, [period, sourceKey]);

  const attention = useMemo(
    () =>
      buildAttentionItems({ p3, matrix, settlements, stock, recon }),
    [p3, matrix, settlements, stock, recon],
  );

  // Indicadores — só valores cuja definição está comprovada.
  const divergenceCount = attention.filter(
    (i) => i.kind === "divergence",
  ).length;
  const unverifiedCount = attention.filter(
    (i) => i.kind !== "divergence",
  ).length;
  const divergenceUnknown =
    p3?.kind === "error" ||
    settlements?.kind === "error" ||
    stock?.kind === "error" ||
    recon?.kind === "error";
  // «Divergências identificadas» só exibe um número quando a contagem
  // é comprovada: zero com verificações pendentes seria um falso
  // negativo — INCONCLUSIVE/pendente nunca vira «0» (REWORK-011).
  const divergenceValue =
    divergenceCount > 0
      ? String(divergenceCount)
      : divergenceUnknown || unverifiedCount > 0
        ? "—"
        : "0";
  const divergenceHint =
    divergenceCount > 0
      ? unverifiedCount > 0
        ? "diferenças comprovadas — outras verificações pendentes"
        : "diferenças comprovadas nas conferências"
      : divergenceUnknown
        ? "nem todas as fontes responderam"
        : unverifiedCount > 0
          ? "não verificadas — conferências pendentes"
          : "nenhuma diferença comprovada nas conferências";
  const operandStatus = (
    key: "entradasSaidas" | "p7" | "h02",
  ): string | null =>
    recon?.kind === "ready"
      ? (recon.data.operands[key].status ?? null)
      : null;
  const reportAvailable = (key: ReportKey): boolean => {
    if (key === "financial-settlements") {
      return settlements?.kind === "ready";
    }
    if (key === "stock-inventory") {
      return (
        stock?.kind === "ready" &&
        stock.data.status !== "source_missing"
      );
    }
    const operand =
      key === "stock-movements" ? "entradasSaidas" : "h02";
    return operandStatus(operand) === "AVAILABLE";
  };
  const availableReports = CATALOG_REPORT_KEYS.filter(
    reportAvailable,
  ).length;

  const scrollTo = (id: string) => {
    const node = document.getElementById(id);
    if (node) {
      node.scrollIntoView?.({ block: "start" });
      node.focus({ preventScroll: true });
    }
  };

  const [expandedAttention, setExpandedAttention] = useState<
    string | null
  >(null);

  if (!period) {
    return (
      <CfEmptyState
        classNames={cfEmptyStateClassNames}
        defaultMessage="Selecione um mês de referência para consultar os relatórios."
      />
    );
  }

  return (
    <div className="cf-page-stack" aria-label="Relatórios e divergências">
      <CfSectionCard
        title="Relatórios e divergências"
        subtitle="Analise os resultados do mês e identifique o que precisa ser corrigido."
        hint={CF_HELP.monthlyClosing.reportsIndicators}
      >
        <div
          className="cf-monthly-indicators"
          aria-label="Indicadores de relatórios"
        >
          <CfInteractiveDataCard
            ariaLabel={`Divergências identificadas: ${divergenceValue}`}
            fields={[
              {
                id: "value",
                label: "Divergências identificadas",
                value: divergenceValue,
                valueTone: "value",
                present: true,
                hint: divergenceHint,
              },
            ]}
            openHint="Ver na área de atenção"
            onActivate={() => scrollTo("cf-reports-attention")}
          />
          <CfInteractiveDataCard
            ariaLabel={`Relatórios disponíveis: ${availableReports}`}
            fields={[
              {
                id: "value",
                label: "Relatórios disponíveis",
                value: anyLoading ? "—" : String(availableReports),
                valueTone: "value",
                present: true,
                hint: "famílias com consulta autorizada",
              },
            ]}
            openHint="Ver catálogo"
            onActivate={() => scrollTo("cf-reports-catalog")}
          />
          <CfInteractiveDataCard
            ariaLabel={`Fontes não verificadas: ${unverifiedCount}`}
            fields={[
              {
                id: "value",
                label: "Fontes não verificadas",
                value: anyLoading ? "—" : String(unverifiedCount),
                valueTone: "value",
                present: true,
                hint: "fontes indisponíveis ou conferências pendentes",
              },
            ]}
            openHint="Ver na área de atenção"
            onActivate={() => scrollTo("cf-reports-attention")}
          />
        </div>
      </CfSectionCard>

      <CfSectionCard
        title="O que precisa de atenção"
        hint={CF_HELP.monthlyClosing.reportsAttention}
      >
        <div className="cf-settlements-actions">
          <CfActionButton variant="ghost" onClick={reload}>
            Atualizar dados
          </CfActionButton>
        </div>
        <section
          id="cf-reports-attention"
          tabIndex={-1}
          aria-label="Área de atenção"
        >
          {anyLoading ? (
            <p aria-live="polite">Consultando fontes…</p>
          ) : attention.length === 0 ? (
            <CfEmptyState
              classNames={cfEmptyStateClassNames}
              defaultMessage="Nenhuma divergência ou pendência identificada para este período."
            />
          ) : (
            <ul className="cf-attention-list">
              {attention.map((item) => (
                <AttentionRow
                  key={item.id}
                  item={item}
                  expanded={expandedAttention === item.id}
                  onToggle={() =>
                    setExpandedAttention((current) =>
                      current === item.id ? null : item.id,
                    )
                  }
                  onOpenReport={onOpenReport}
                />
              ))}
            </ul>
          )}
        </section>
      </CfSectionCard>

      {/* Conciliação analítica — composição BFF dos três relatórios
          operacionais; distinta da conciliação governada P3. */}
      <AnalyticalReconciliationSection
        reconciliation={recon?.kind === "ready" ? recon.data : null}
        loading={recon === null}
      />

      {/* Catálogo compacto — cada cartão abre a página contextual do
          relatório dentro do Fechamento Mensal (sem rótulos repetidos). */}
      <CfSectionCard
        title="Relatórios para análise"
        subtitle="Abra a página do relatório para ver totais, agrupamentos e registros."
        hint={CF_HELP.monthlyClosing.reportsCatalog}
      >
        <div
          id="cf-reports-catalog"
          tabIndex={-1}
          className="cf-report-cards"
          aria-label="Catálogo de relatórios"
        >
          {CATALOG_REPORT_KEYS.map((key) => {
            const meta = REPORT_META[key];
            let status: string | null;
            let updated: Date | null = null;
            if (key === "financial-settlements") {
              status =
                settlements?.kind === "ready"
                  ? "Disponível"
                  : settlements?.kind === "error"
                    ? "Indisponível"
                    : null;
              updated =
                settlements?.kind === "ready" ? settlements.at : null;
            } else if (key === "stock-inventory") {
              status =
                stock?.kind === "ready"
                  ? (STOCK_STATUS_LABELS[stock.data.status] ??
                    "Disponível")
                  : stock?.kind === "error"
                    ? "Indisponível"
                    : null;
              updated = stock?.kind === "ready" ? stock.at : null;
            } else {
              // R05/R08 — disponibilidade derivada da conciliação
              // analítica (a BFF consulta cada produtor e classifica
              // o operando; fonte ausente nunca entra como zero).
              const operand =
                key === "stock-movements" ? "entradasSaidas" : "h02";
              status =
                recon?.kind === "ready"
                  ? (OPERAND_STATUS_LABELS[
                      recon.data.operands[operand].status ?? ""
                    ] ?? "Disponível")
                  : recon?.kind === "error"
                    ? "Indisponível"
                    : null;
              updated = recon?.kind === "ready" ? recon.at : null;
            }
            const selected =
              selectedReport === REPORT_KEY_TO_FAMILY[key];
            return (
              <CfInteractiveDataCard
                key={key}
                className={
                  selected ? "cf-report-card--selected" : undefined
                }
                ariaLabel={`${meta.name}${
                  selected ? " — último relatório aberto" : ""
                }`}
                openHint="Abrir relatório"
                onActivate={() => onOpenReport(key)}
              >
                <div className="cf-report-card">
                  <strong className="cf-report-card__name">
                    {meta.name}
                  </strong>
                  <span className="cf-report-card__desc">
                    {meta.description}
                  </span>
                  <span className="cf-report-card__meta">
                    <CfStatusBadge
                      label={status ?? "—"}
                      variant={
                        status === "Disponível"
                          ? "success"
                          : status !== null &&
                              status !== "Parcialmente disponível" &&
                              status !== "Sem dados para o filtro"
                            ? "warning"
                            : "info"
                      }
                    />
                    {updated
                      ? `Atualizado em ${formatDateTime(
                          updated.toISOString(),
                        )}`
                      : meta.origin}
                  </span>
                </div>
              </CfInteractiveDataCard>
            );
          })}
        </div>
      </CfSectionCard>

      {/* Matriz R01–R15 — rastreabilidade técnica preservada fora do
          fluxo visual principal (§26.3). */}
      <details className="cf-disclosure">
        <summary className="cf-disclosure__summary">
          Cobertura da matriz R01–R15 — rastreabilidade técnica
        </summary>
        <div className="cf-disclosure__body">
          {matrix?.kind === "ready" ? (
            <table
              className="cf-p3-table"
              aria-label="Cobertura dos relatórios R01 a R15"
            >
              <thead>
                <tr>
                  <th>Relatório</th>
                  <th>Fonte</th>
                  <th>Itens</th>
                  <th>Cobertura</th>
                </tr>
              </thead>
              <tbody>
                {matrix.data.reports.map((entry) => (
                  <tr key={entry.report_id}>
                    <td>
                      {entry.report_id} — {entry.label}
                    </td>
                    <td>{SOURCE_LABELS[entry.source_kind]}</td>
                    <td>
                      {entry.checklist_items > 0
                        ? `${entry.items_validated}/${entry.checklist_items}`
                        : "—"}
                    </td>
                    <td>
                      <CfStatusBadge
                        label={COVERAGE_LABELS[entry.coverage]}
                        variant={COVERAGE_VARIANTS[entry.coverage]}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : matrix?.kind === "not_opened" ? (
            <CfFeedbackMessage intent="info" title="Matriz de entregáveis">
              A competência ainda não foi aberta — a cobertura dos
              relatórios R01–R15 não foi gerada para este período.
            </CfFeedbackMessage>
          ) : matrix?.kind === "error" ? (
            <CfQueryErrorBanner
              error={matrix.error}
              dataset="a matriz de relatórios"
              onRetry={reload}
            />
          ) : (
            <p aria-live="polite">Consultando a matriz de relatórios…</p>
          )}
        </div>
      </details>
    </div>
  );
}
