/**
 * Corpo render-only do cockpit da competência — compartilhado pela
 * página `CockpitPage` e pela aba «Visão geral» do Fechamento mensal.
 * Estados reais de P2, P3, P4 e P5 derivados do backend: fonte
 * indisponível aparece como bloqueio, nunca como sucesso.
 */
import type { Cockpit } from "../../api/packagesApi";
import {
  CfEmptyState,
  CfSectionCard,
  CfStatusBadge,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { CF_HELP } from "../../content/helpTooltips";

const CLOSING_LABELS: Record<string, string> = {
  PENDING: "Fechamento pendente",
  MONTHLY_CLOSING_COMPLETED: "Fechamento mensal concluído",
  TERMINALLY_REJECTED: "Competência rejeitada (terminal)",
};

const PACKAGE_LABELS: Record<string, string> = {
  PACKAGE_INCOMPLETE: "Pacote incompleto",
  PACKAGE_FINALIZED: "Pacote finalizado",
  PACKAGE_SUBMITTED_FOR_REVIEW: "Enviado para análise",
};

const VARIANTS: Record<
  string,
  "warning" | "info" | "success" | "neutral" | "danger"
> = {
  MONTHLY_CLOSING_COMPLETED: "success",
  TERMINALLY_REJECTED: "danger",
  PENDING: "warning",
  AVAILABLE: "success",
  OFFICIAL: "success",
  UNAVAILABLE: "danger",
  DECLARED: "warning",
};

const ITEM_STATE_LABELS: Record<string, string> = {
  EXPECTED: "Aguardando evidência",
  ACCEPTED: "Aceitos",
  NOT_APPLICABLE: "Não aplicáveis",
  CANCELLED: "Cancelados",
};

export function countOpenPendencies(cockpit: Cockpit | null): number {
  return Object.entries(cockpit?.p4_pendencies ?? {}).reduce(
    (sum, [state, n]) =>
      ["OPEN", "IN_ANALYSIS", "WAITING_EXTERNAL"].includes(state)
        ? sum + n
        : sum,
    0,
  );
}

export function CockpitSummaryPanel({ cockpit }: { cockpit: Cockpit }) {
  const openPendencies = countOpenPendencies(cockpit);

  return (
    <>
      <CfSectionCard title="Conclusão mensal" hint={CF_HELP.cockpit.closing}>
        <p>
          <CfStatusBadge
            variant={VARIANTS[cockpit.closing.state] ?? "neutral"}
            label={CLOSING_LABELS[cockpit.closing.state] ?? cockpit.closing.state}
          />
        </p>
        {cockpit.closing.blocking_reasons.length > 0 ? (
          <ul className="cf-blockers-list">
            {cockpit.closing.blocking_reasons.map((r) => (
              <li key={r}>{r}</li>
            ))}
          </ul>
        ) : null}
      </CfSectionCard>

      <CfSectionCard
        title="Checklist e evidências (P2)"
        hint={CF_HELP.cockpit.checklist}
      >
        <ul>
          {Object.entries(cockpit.checklist).map(([state, n]) => (
            <li key={state}>
              {ITEM_STATE_LABELS[state] ?? state}: {n}
            </li>
          ))}
        </ul>
      </CfSectionCard>

      <CfSectionCard title="Cutoff e conciliação (P3)" hint={CF_HELP.cockpit.p3}>
        <p>
          Cutoff:{" "}
          {cockpit.p3.cutoff_confirmed ? "confirmado" : "não confirmado"}
        </p>
        <ul>
          {cockpit.p3.domains.map((d) => (
            <li key={d.domain}>
              {d.domain}:{" "}
              <CfStatusBadge
                variant={VARIANTS[d.source_state] ?? "neutral"}
                label={d.source_state}
              />{" "}
              {d.provenance_kind ? (
                <CfStatusBadge
                  variant={VARIANTS[d.provenance_kind] ?? "neutral"}
                  label={
                    d.provenance_kind === "OFFICIAL" ? "oficial" : "declarado"
                  }
                />
              ) : null}{" "}
              {d.divergence !== null ? `divergência ${d.divergence}` : ""}
            </li>
          ))}
        </ul>
      </CfSectionCard>

      <CfSectionCard title="Pendências (P4)" hint={CF_HELP.cockpit.p4}>
        <p>{openPendencies} pendência(s) em aberto</p>
        <ul>
          {Object.entries(cockpit.p4_pendencies).map(([state, n]) => (
            <li key={state}>
              {state}: {n}
            </li>
          ))}
        </ul>
      </CfSectionCard>

      <CfSectionCard title="Pacotes (P5)" hint={CF_HELP.cockpit.p5}>
        {cockpit.closing.packages.length === 0 ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Nenhum pacote aplicável na competência."
          />
        ) : (
          <ul>
            {cockpit.closing.packages.map((pkg) => (
              <li key={pkg.recipient_area}>
                {pkg.recipient_area}:{" "}
                <CfStatusBadge
                  variant="neutral"
                  label={PACKAGE_LABELS[pkg.state] ?? pkg.state}
                />{" "}
                {pkg.review_state}
              </li>
            ))}
          </ul>
        )}
      </CfSectionCard>
    </>
  );
}
