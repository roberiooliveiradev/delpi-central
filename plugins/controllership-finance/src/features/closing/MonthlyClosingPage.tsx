/**
 * Fechamento mensal — workspace da competência com exatamente três abas
 * (Visão geral / Documentos e interações / Relatórios e divergências),
 * conforme decisão visual do PO no doc 112 §§25–26.
 *
 * Composição apenas: a aba Visão geral reutiliza o cockpit real P1–P5,
 * Documentos e interações reutiliza o painel de evidências P2 e
 * Relatórios e divergências reutiliza a matriz R01–R15. Nenhum dado,
 * indicador ou comportamento de domínio é criado aqui — «—» significa
 * dado ainda não carregado, nunca zero confirmado.
 */
import { useCallback, useEffect, useState } from "react";

import { ApiError } from "../../api/httpClient";
import {
  getClosingCockpit,
  type Cockpit,
} from "../../api/packagesApi";
import {
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  FilterInputField,
  FiltersRow,
} from "../../app/cfFiltersUi";
import { ClosingHero } from "../../app/ClosingHero";
import {
  CfActionButton,
  CfEmptyState,
  CfInteractiveDataCard,
  CfSectionCard,
  CfSegmentToggle,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  navigatePluginPath,
  navigatePluginView,
} from "../../app/pluginNavigation";
import { normalizeBasePath } from "../../app/pluginRoutes";
import { CF_HELP } from "../../content/helpTooltips";
import { ClosingDocumentsPanel } from "./ClosingDocumentsPanel";
import { CockpitSummaryPanel } from "./CockpitSummaryPanel";
import { ReportsMatrixPanel } from "./ReportsMatrixPanel";

type PanelError = { status: number; code: string | null; message: string };

type MonthlyClosingTab = "overview" | "documents" | "reports";

const PERIOD_PATTERN = /^\d{4}-(0[1-9]|1[0-2])$/;

const TAB_OPTIONS = [
  { value: "overview", label: "Visão geral" },
  { value: "documents", label: "Documentos e interações" },
  { value: "reports", label: "Relatórios e divergências" },
] as const;

const TAB_SEARCH: Record<Exclude<MonthlyClosingTab, "overview">, string> = {
  documents: "tab=documents",
  reports: "tab=reports",
};

const ERROR_MESSAGES: Record<string, string> = {
  forbidden: "Você não tem autorização para esta consulta.",
  unauthorized: "Sessão expirada — autentique-se novamente.",
  competence_not_opened: "Competência não aberta.",
};

const ZERO_DIVERGENCE_PATTERN = /^-?0+([.,]0+)?$/;

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

function parseTab(search: string): MonthlyClosingTab {
  const value = new URLSearchParams(search).get("tab");
  if (value === "documents" || value === "reports") return value;
  return "overview";
}

function countDivergences(cockpit: Cockpit | null): number | null {
  if (!cockpit) return null;
  return cockpit.p3.domains.filter(
    (d) =>
      d.divergence !== null && !ZERO_DIVERGENCE_PATTERN.test(d.divergence),
  ).length;
}

function indicatorValue(count: number | null): string {
  return count === null ? "—" : String(count);
}

export function MonthlyClosingPage({
  basePath,
  period: initialPeriod,
}: {
  basePath: string;
  period?: string;
}) {
  const [period, setPeriod] = useState(
    initialPeriod && PERIOD_PATTERN.test(initialPeriod)
      ? initialPeriod
      : currentCompetence(),
  );
  const [tab, setTab] = useState<MonthlyClosingTab>(() =>
    typeof window !== "undefined"
      ? parseTab(window.location.search)
      : "overview",
  );
  const [cockpit, setCockpit] = useState<Cockpit | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<PanelError | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const periodValid = PERIOD_PATTERN.test(period);
  const base = normalizeBasePath(basePath);

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
  }, [reload]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const syncTab = () => setTab(parseTab(window.location.search));
    window.addEventListener("popstate", syncTab);
    return () => window.removeEventListener("popstate", syncTab);
  }, []);

  const selectTab = useCallback(
    (next: MonthlyClosingTab) => {
      setTab(next);
      navigatePluginView("monthly_closing", {
        basePath: base,
        search: next === "overview" ? undefined : TAB_SEARCH[next],
      });
    },
    [base],
  );

  const blockingCount = cockpit?.closing.blocking_reasons.length ?? null;
  const divergenceCount = countDivergences(cockpit);
  const documentsCount = cockpit ? (cockpit.checklist.EXPECTED ?? 0) : null;

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Fechamento mensal"
    >
      <ClosingHero
        title={
          <CfTitleWithHelp
            title="Fechamento mensal"
            hint={CF_HELP.monthlyClosing.page}
          />
        }
        subtitle="Bancada de trabalho da competência: visão geral, documentos e relatórios do fechamento."
        filters={
          <form
            className="cf-settlements-filters"
            onSubmit={(event) => event.preventDefault()}
          >
            <FiltersRow>
              <FilterInputField
                id="cf-monthly-closing-period"
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

      <div
        className="cf-monthly-indicators"
        aria-label="Indicadores de atenção"
      >
        <CfInteractiveDataCard
          ariaLabel={`Bloqueios: ${indicatorValue(blockingCount)}`}
          fields={[
            {
              id: "value",
              label: "Bloqueios",
              value: indicatorValue(blockingCount),
              valueTone: "value",
              present: true,
            },
          ]}
          openHint="Ver na Visão geral"
          onActivate={() => selectTab("overview")}
        />
        <CfInteractiveDataCard
          ariaLabel={`Divergências: ${indicatorValue(divergenceCount)}`}
          fields={[
            {
              id: "value",
              label: "Divergências",
              value: indicatorValue(divergenceCount),
              valueTone: "value",
              present: true,
            },
          ]}
          openHint="Ver em Relatórios e divergências"
          onActivate={() => selectTab("reports")}
        />
        <CfInteractiveDataCard
          ariaLabel={`Documentos a tratar: ${indicatorValue(documentsCount)}`}
          fields={[
            {
              id: "value",
              label: "Documentos a tratar",
              value: indicatorValue(documentsCount),
              valueTone: "value",
              present: true,
            },
          ]}
          openHint="Ver em Documentos e interações"
          onActivate={() => selectTab("documents")}
        />
      </div>

      <CfSegmentToggle<MonthlyClosingTab>
        options={TAB_OPTIONS}
        value={tab}
        onChange={selectTab}
        ariaLabel="Visões do fechamento mensal"
        size="sm"
      />

      <div className="cf-page-stack" aria-busy={loading}>
        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="o fechamento mensal da competência"
            onRetry={reload}
          />
        ) : null}

        {tab === "overview" ? (
          <>
            {loading && !cockpit ? (
              <p aria-live="polite">Carregando visão geral…</p>
            ) : null}
            {!loading && !cockpit && !error ? (
              <CfEmptyState
                classNames={cfEmptyStateClassNames}
                defaultMessage="Sem dados de fechamento para a competência."
              />
            ) : null}
            {cockpit ? <CockpitSummaryPanel cockpit={cockpit} /> : null}
          </>
        ) : null}

        {tab === "documents" ? (
          <>
            <ClosingDocumentsPanel period={period} />
            <CfSectionCard title="Checklist da competência">
              <p>
                A validação item a item do checklist P2 permanece na página
                dedicada.
              </p>
              <CfActionButton
                variant="ghost"
                onClick={() =>
                  navigatePluginPath(`${base}/closing/checklist/${period}`)
                }
              >
                Abrir checklist da competência
              </CfActionButton>
            </CfSectionCard>
          </>
        ) : null}

        {tab === "reports" ? (
          <>
            <ReportsMatrixPanel period={period} />
            <CfSectionCard title="Consultas operacionais">
              <ul className="cf-monthly-report-links">
                <li>
                  <CfActionButton
                    variant="ghost"
                    onClick={() =>
                      navigatePluginView("financial_settlements", {
                        basePath: base,
                      })
                    }
                  >
                    Baixas financeiras
                  </CfActionButton>
                </li>
                <li>
                  <CfActionButton
                    variant="ghost"
                    onClick={() =>
                      navigatePluginView("stock_inventory", {
                        basePath: base,
                      })
                    }
                  >
                    Estoque histórico — P7
                  </CfActionButton>
                </li>
              </ul>
            </CfSectionCard>
            <CfSectionCard
              title="Prévia do PDF"
              hint={CF_HELP.monthlyClosing.pdfPreview}
            >
              <div
                className="cf-pdf-preview-slot"
                aria-label="Prévia do PDF indisponível"
              >
                <p>
                  A prévia dos relatórios em PDF será exibida aqui em uma
                  versão futura.
                </p>
              </div>
            </CfSectionCard>
          </>
        ) : null}
      </div>
    </section>
  );
}
