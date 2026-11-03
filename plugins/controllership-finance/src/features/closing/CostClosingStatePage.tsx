/**
 * Acompanhamento do fechamento — visão de apoio R12/R15 (docs 129/151).
 *
 * Design aprovado pelo PO: sinais técnicos do ERP por filial em
 * linguagem de negócio. Marcador técnico nunca é homologação nem
 * execução de rotina — a validação final é da equipe responsável.
 */
import { useCallback, useEffect, useState } from "react";
import {
  CalendarCheck,
  Coins,
  Info,
  Loader2,
  Store,
  Users,
} from "lucide-react";

import { ApiError } from "../../api/httpClient";
import {
  getCostClosingState,
  type ClosingStateBranch,
  type ClosingStateNode,
  type ClosingStateNodeState,
  type CostClosingStatePayload,
} from "../../api/costClosingStateApi";
import {
  CfEmptyState,
  CfLoadingCard,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { ClosingHero } from "../../app/ClosingHero";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import { formatCivilDate } from "../../utils/formatters";
import { CF_HELP } from "../../content/helpTooltips";

type AsyncData =
  | { kind: "ready"; data: CostClosingStatePayload; at: Date }
  | {
      kind: "error";
      error: { status: number; code: string | null; message: string };
    }
  | null;

type BadgeVariant = "neutral" | "info" | "success" | "warning" | "danger";

type CheckRow = {
  key: keyof ClosingStateBranch;
  title: string;
  description: string;
  /** Rótulo do badge quando há evidência (available/observed). */
  evidenceLabel: string;
  icon: typeof Store;
};

const CHECK_ROWS: CheckRow[] = [
  {
    key: "snapshot",
    title: "Posição de estoque do fechamento",
    description: "Com base nos registros do sistema.",
    evidenceLabel: "Encontrado",
    icon: Store,
  },
  {
    key: "cutoff_marker",
    title: "Referência do último fechamento",
    description: "Data e referência registradas no sistema.",
    evidenceLabel: "Encontrada",
    icon: CalendarCheck,
  },
  {
    key: "cost_evidence",
    title: "Lançamentos de custo",
    description: "Registros de custos identificados.",
    evidenceLabel: "Encontrados",
    icon: Coins,
  },
  {
    key: "wizard_lifecycle",
    title: "Andamento do processo",
    description: "Situação do fechamento no sistema.",
    evidenceLabel: "Encontrado",
    icon: Loader2,
  },
  {
    key: "human_acceptance",
    title: "Validação da equipe",
    description: "Confirmação da equipe responsável.",
    evidenceLabel: "Informada",
    icon: Users,
  },
];

const EVIDENCE_STATES: ClosingStateNodeState[] = ["available", "observed"];

function nodePresentation(
  node: ClosingStateNode | undefined,
  evidenceLabel: string,
): { label: string; variant: BadgeVariant } {
  const state = node?.state;
  if (!state) return { label: "Sem informação", variant: "neutral" };
  if (EVIDENCE_STATES.includes(state)) {
    return { label: evidenceLabel, variant: "success" };
  }
  switch (state) {
    case "missing":
      return { label: "Não encontrado", variant: "warning" };
    case "partial":
      return { label: "Parcial", variant: "warning" };
    case "not_advanced":
      return { label: "Não avançado", variant: "neutral" };
    case "not_informed":
      return { label: "Pendente de informação", variant: "warning" };
    default:
      return { label: "Sem informação", variant: "neutral" };
  }
}

function evidenceCount(nodes: ClosingStateBranch): number {
  return CHECK_ROWS.filter((row) =>
    EVIDENCE_STATES.includes(nodes[row.key]?.state),
  ).length;
}

function branchSummary(count: number): {
  label: string;
  variant: BadgeVariant;
} {
  if (count === CHECK_ROWS.length) {
    return { label: "Evidências completas", variant: "info" };
  }
  if (count === 0) {
    return { label: "Sem evidências registradas", variant: "neutral" };
  }
  return { label: "Acompanhamento parcial", variant: "warning" };
}

function BranchCard({
  branch,
  nodes,
}: {
  branch: string;
  nodes: ClosingStateBranch;
}) {
  const count = evidenceCount(nodes);
  const summary = branchSummary(count);
  return (
    <CfSectionCard
      title={`Filial ${branch}`}
      subtitle={`${count} de ${CHECK_ROWS.length} verificações com evidência`}
      actions={
        <CfStatusBadge label={summary.label} variant={summary.variant} />
      }
    >
      <ul
        className="cf-r12-checks"
        aria-label={`Verificações da filial ${branch}`}
      >
        {CHECK_ROWS.map((row) => {
          const node = nodes[row.key];
          const presentation = nodePresentation(node, row.evidenceLabel);
          const Icon = row.icon;
          return (
            <li key={row.key} className="cf-r12-check">
              <span className="cf-r12-check__icon" aria-hidden="true">
                <Icon size={18} strokeWidth={1.8} />
              </span>
              <span className="cf-r12-check__text">
                <span className="cf-r12-check__title">{row.title}</span>
                <span className="cf-r12-check__desc">
                  {row.description}
                </span>
              </span>
              <CfStatusBadge
                label={presentation.label}
                variant={presentation.variant}
              />
            </li>
          );
        })}
      </ul>
    </CfSectionCard>
  );
}

export function CostClosingStatePage({
  reportContext,
}: {
  reportContext: { period: string };
}) {
  const period = reportContext.period;
  const [state, setState] = useState<AsyncData>(null);

  const load = useCallback(() => {
    setState(null);
    getCostClosingState(period)
      .then((data) => setState({ kind: "ready", data, at: new Date() }))
      .catch((err: unknown) => {
        const e =
          err instanceof ApiError
            ? {
                status: err.status,
                code: err.code ?? null,
                message: err.message,
              }
            : {
                status: 0,
                code: null,
                message: "Falha ao consultar o estado.",
              };
        setState({ kind: "error", error: e });
      });
  }, [period]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="cf-page-stack" aria-label="Acompanhamento do fechamento">
      <ClosingHero
        title={
          <span className="cf-r12-hero-title">
            <span className="cf-r12-hero-chips">
              <CfStatusBadge label="Visão de apoio" variant="info" />
              <CfStatusBadge label="R12/R15" variant="neutral" />
            </span>
            <CfTitleWithHelp
              title="Acompanhamento do fechamento"
              hint={CF_HELP.costClosingState.page}
            />
          </span>
        }
        subtitle="Resumo dos sinais encontrados no sistema para apoiar a conferência do fechamento por filial."
        updatedAt={state?.kind === "ready" ? state.at : null}
        onRefresh={load}
        refreshing={state === null}
        filters={null}
      />
      {state === null ? (
        <CfLoadingCard
          title="Consultando o acompanhamento do fechamento…"
          variant="compact"
        />
      ) : state.kind === "error" ? (
        <CfQueryErrorBanner
          error={state.error}
          dataset="o acompanhamento do fechamento"
          onRetry={load}
        />
      ) : (
        <>
          <CfFeedbackMessage intent="info" title="Como interpretar esta tela">
            <ul className="cf-r12-guide">
              <li>
                Esta tela mostra sinais encontrados no sistema para apoiar
                a análise do fechamento.
              </li>
              <li>
                Ela não confirma sozinha que o fechamento foi concluído.
              </li>
              <li>
                A validação final depende da conferência da equipe
                responsável.
              </li>
            </ul>
          </CfFeedbackMessage>
          {Object.keys(state.data.branches ?? {}).length === 0 ? (
            <CfEmptyState
              classNames={cfEmptyStateClassNames}
              defaultMessage="Nenhum sinal de fechamento encontrado para este período e escopo."
            />
          ) : (
            <div className="cf-r12-branch-grid">
              {Object.entries(state.data.branches)
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([branch, nodes]) => (
                  <BranchCard
                    key={branch}
                    branch={branch}
                    nodes={nodes}
                  />
                ))}
            </div>
          )}
          <footer className="cf-r12-footer">
            <p className="cf-report-card__meta">
              <Info
                size={14}
                aria-hidden="true"
                className="cf-r12-footer__icon"
              />{" "}
              Base consultada: posição de{" "}
              {state.data.referenceDate
                ? formatCivilDate(state.data.referenceDate)
                : "—"}{" "}
              · visão de apoio ao fechamento
            </p>
            <details className="cf-r12-details">
              <summary>Detalhes técnicos e limitações</summary>
              <ul>
                {(state.data.limitations ?? []).map((lim) => (
                  <li key={lim}>{lim}</li>
                ))}
                {Object.entries(state.data.branches ?? {}).flatMap(
                  ([branch, nodes]) =>
                    CHECK_ROWS.flatMap((row) =>
                      (nodes[row.key]?.limitations ?? []).map((lim) => (
                        <li key={`${branch}-${row.key}-${lim}`}>
                          Filial {branch}: {lim}
                        </li>
                      )),
                    ),
                )}
              </ul>
              <p className="cf-report-card__meta">
                <CfTitleWithHelp
                  title="Proveniência"
                  hint={CF_HELP.costClosingState.provenance}
                />{" "}
                estado {state.data.officiality ?? "—"} · marcadores
                técnicos, nunca homologação.
              </p>
            </details>
          </footer>
        </>
      )}
    </div>
  );
}
