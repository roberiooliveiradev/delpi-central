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
  CfSectionLoading,
} from "../../app/cfFeedbackUi";
import {
  CfEmptyState,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  FilterInputField,
  FiltersRow,
} from "../../app/cfFiltersUi";
import { ClosingHero } from "../../app/ClosingHero";
import { CF_HELP } from "../../content/helpTooltips";
import { CockpitSummaryPanel } from "./CockpitSummaryPanel";

type PanelError = { status: number; code: string | null; message: string };

const PERIOD_PATTERN = /^\d{4}-(0[1-9]|1[0-2])$/;

const ERROR_MESSAGES: Record<string, string> = {
  forbidden: "Você não tem autorização para esta consulta.",
  unauthorized: "Sessão expirada — autentique-se novamente.",
  competence_not_opened: "Competência não aberta.",
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
          <CfSectionLoading label="Carregando cockpit…" variant="panel" />
        ) : null}
        {!loading && !cockpit && !error ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Sem dados de cockpit para a competência."
          />
        ) : null}

        {cockpit ? <CockpitSummaryPanel cockpit={cockpit} /> : null}
      </div>
    </section>
  );
}
