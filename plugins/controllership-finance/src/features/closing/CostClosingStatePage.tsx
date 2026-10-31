/**
 * Estado de fechamento de custos e cutoff — R12/R15 (doc 129).
 *
 * Trilha de nós independentes por filial — semântica aprovada C3-D02=A:
 * snapshot SB9010, marcador MV_ULMES, evidência TTAT, lifecycle do
 * wizard (indisponível — E12.5) e homologação humana (não informada —
 * C3-D05). Marcador técnico nunca é homologação nem execução ERP.
 */
import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../../api/httpClient";
import {
  getCostClosingState,
  type ClosingStateBranch,
  type ClosingStateNode,
  type CostClosingStatePayload,
} from "../../api/costClosingStateApi";
import {
  CfEmptyState,
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
import { CF_HELP } from "../../content/helpTooltips";

type AsyncData =
  | { kind: "ready"; data: CostClosingStatePayload; at: Date }
  | { kind: "error"; error: { status: number; code: string | null; message: string } }
  | null;

const NODE_LABELS: Record<keyof ClosingStateBranch, string> = {
  snapshot: "Snapshot de estoque (SB9010)",
  cutoff_marker: "Marcador de último fechamento (MV_ULMES)",
  cost_evidence: "Evidência de custos (escritas TTAT)",
  wizard_lifecycle: "Ciclo de vida do wizard",
  human_acceptance: "Homologação humana",
};

const STATE_LABELS: Record<string, string> = {
  available: "Disponível",
  missing: "Snapshot ausente",
  partial: "Parcial",
  observed: "Observado",
  not_advanced: "Não avançado",
  unavailable: "Indisponível",
  not_informed: "Não informado",
};

function nodeBadgeVariant(node: ClosingStateNode): "success" | "warning" | "info" {
  if (node.state === "available" || node.state === "observed") {
    return "success";
  }
  if (node.state === "partial" || node.state === "not_advanced") {
    return "warning";
  }
  return "info";
}

function BranchStateSection({
  branch,
  nodes,
}: {
  branch: string;
  nodes: ClosingStateBranch;
}) {
  return (
    <CfSectionCard title={`Filial ${branch}`}>
      <ul className="cf-closing-state-nodes" aria-label={`Estado filial ${branch}`}>
        {(Object.keys(NODE_LABELS) as (keyof ClosingStateBranch)[]).map(
          (key) => {
            const node = nodes[key];
            return (
              <li key={key}>
                <span>{NODE_LABELS[key]}</span>
                <CfStatusBadge
                  label={STATE_LABELS[node.state] ?? node.state}
                  variant={nodeBadgeVariant(node)}
                />
              </li>
            );
          },
        )}
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
            ? { status: err.status, code: err.code ?? null, message: err.message }
            : { status: 0, code: null, message: "Falha ao consultar o estado." };
        setState({ kind: "error", error: e });
      });
  }, [period]);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="cf-page-stack" aria-label="Estado de fechamento e cutoff">
      <ClosingHero
        title="Estado de fechamento e cutoff — R12/R15"
        subtitle="Marcadores técnicos observados no ERP por filial. Não é homologação nem execução de rotina."
        hint={CF_HELP.costClosingState.page}
      />
      {state === null ? (
        <p aria-live="polite">Consultando o estado de fechamento…</p>
      ) : state.kind === "error" ? (
        <CfQueryErrorBanner
          error={state.error}
          dataset="o estado de fechamento"
          onRetry={load}
        />
      ) : (
        <>
          <CfFeedbackMessage intent="info" title="Limitações desta visão">
            <ul>
              {(state.data.limitations ?? []).map((lim) => (
                <li key={lim}>{lim}</li>
              ))}
            </ul>
          </CfFeedbackMessage>
          {Object.keys(state.data.branches ?? {}).length === 0 ? (
            <CfEmptyState
              classNames={cfEmptyStateClassNames}
              defaultMessage="Nenhum marcador de fechamento observado para este período e escopo."
            />
          ) : (
            Object.entries(state.data.branches)
              .sort(([a], [b]) => a.localeCompare(b))
              .map(([branch, nodes]) => (
                <BranchStateSection
                  key={branch}
                  branch={branch}
                  nodes={nodes}
                />
              ))
          )}
          <p className="cf-report-card__meta">
            <CfTitleWithHelp
              title="Proveniência"
              hint={CF_HELP.costClosingState.provenance}
            />{" "}
            snapshot {state.data.referenceDate ?? "—"} · oficialidade{" "}
            {state.data.officiality}
          </p>
        </>
      )}
    </div>
  );
}
