/**
 * Cockpit da competência — estados reais de P2 (checklist), P3
 * (cutoff/conciliação), P4 (pendências) e P5 (pacotes/conclusão).
 * Render-only: o backend deriva cada estado; fonte indisponível aparece
 * como bloqueio, nunca como sucesso.
 */
import {
  useCallback,
  useEffect,
  useState,
} from "react";

import { ApiError } from "../../api/httpClient";
import {
  getClosingCockpit,
  type Cockpit,
} from "../../api/packagesApi";
import {
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  CfEmptyState,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  FilterInputField,
  FiltersRow,
} from "../../app/cfFiltersUi";
import { ClosingHero } from "../../app/ClosingHero";
import { CF_HELP } from "../../content/helpTooltips";

type PanelError = { status: number; code: string | null; message: string };

const PERIOD_PATTERN = /^\d{4}-(0[1-9]|1[0-2])$/;

const ERROR_MESSAGES: Record<string, string> = {
  forbidden: "Você não tem autorização para esta consulta.",
  unauthorized: "Sessão expirada — autentique-se novamente.",
  competence_not_opened: "Competência não aberta.",
};

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

function currentCompetence(): string {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export function CockpitPage({ period: initialPeriod }: { period?: string }) {
  const [period, setPeriod] = useState(
    initialPeriod && PERIOD_PATTERN.test(initialPeriod)
      ? initialPeriod
      : currentCompetence(),
  );
  const [cockpit, setCockpit] = useState<Cockpit | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<PanelError | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const periodValid = PERIOD_PATTERN.test(period);

  const reload = useCallback(async () => {
    if (!periodValid) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getClosingCockpit(period);
      setCockpit(data);
      setLastUpdated(new Date());
    } catch (err) {
      setError(mapError(err));
    } finally {
      setLoading(false);
    }
  }, [period, periodValid]);

  useEffect(() => {
    void reload();
  }, [period]);

  const openPendencies = Object.entries(
    cockpit?.p4_pendencies ?? {},
  ).reduce(
    (sum, [state, n]) =>
      ["OPEN", "IN_ANALYSIS", "WAITING_EXTERNAL"].includes(state)
        ? sum + n
        : sum,
    0,
  );

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Cockpit da competência"
    >
      <ClosingHero
        title={
          <CfTitleWithHelp
            title="Cockpit do fechamento"
            hint={CF_HELP.cockpit.page}
          />
        }
        subtitle="Estado real da competência: checklist, conciliação, pendências, pacotes e conclusão."
        filters={
          <form
            className="cf-settlements-filters"
            onSubmit={(event) => event.preventDefault()}
          >
            <FiltersRow>
              <FilterInputField
                id="cf-cockpit-period"
                label="Competência"
                type="month"
                value={period}
                onChange={setPeriod}
              />
            </FiltersRow>
          </form>
        }
        updatedAt={lastUpdated}
        onRefresh={reload}
        refreshing={loading}
        onClearFilters={() => setPeriod(currentCompetence())}
      />

      <div className="cf-page-stack" aria-busy={loading}>
        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="o cockpit da competência"
            onRetry={reload}
          />
        ) : null}
        {loading && !cockpit ? (
          <p aria-live="polite">Carregando cockpit…</p>
        ) : null}
        {!loading && !cockpit && !error ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Sem dados de cockpit para a competência."
          />
        ) : null}

        {cockpit ? (
          <>
            <CfSectionCard
              title="Conclusão mensal"
              hint={CF_HELP.cockpit.closing}
            >
              <p>
                <CfStatusBadge
                  variant={
                    VARIANTS[cockpit.closing.state] ?? "neutral"
                  }
                  label={
                    CLOSING_LABELS[cockpit.closing.state] ??
                    cockpit.closing.state
                  }
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

            <CfSectionCard
              title="Cutoff e conciliação (P3)"
              hint={CF_HELP.cockpit.p3}
            >
              <p>
                Cutoff:{" "}
                {cockpit.p3.cutoff_confirmed
                  ? "confirmado"
                  : "não confirmado"}
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
                        variant={
                          VARIANTS[d.provenance_kind] ?? "neutral"
                        }
                        label={
                          d.provenance_kind === "OFFICIAL"
                            ? "oficial"
                            : "declarado"
                        }
                      />
                    ) : null}{" "}
                    {d.divergence !== null
                      ? `divergência ${d.divergence}`
                      : ""}
                  </li>
                ))}
              </ul>
            </CfSectionCard>

            <CfSectionCard
              title="Pendências (P4)"
              hint={CF_HELP.cockpit.p4}
            >
              <p>{openPendencies} pendência(s) em aberto</p>
              <ul>
                {Object.entries(cockpit.p4_pendencies).map(
                  ([state, n]) => (
                    <li key={state}>
                      {state}: {n}
                    </li>
                  ),
                )}
              </ul>
            </CfSectionCard>

            <CfSectionCard
              title="Pacotes (P5)"
              hint={CF_HELP.cockpit.p5}
            >
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
                        label={
                          PACKAGE_LABELS[pkg.state] ?? pkg.state
                        }
                      />{" "}
                      {pkg.review_state}
                    </li>
                  ))}
                </ul>
              )}
            </CfSectionCard>
          </>
        ) : null}
      </div>
    </section>
  );
}
