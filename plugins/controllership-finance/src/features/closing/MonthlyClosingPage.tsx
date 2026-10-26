/**
 * Fechamento mensal — workspace da competência com exatamente três abas
 * (Visão geral / Documentos e interações / Relatórios e divergências),
 * conforme decisão visual do PO no doc 112 §§25–26 e rework §28.
 *
 * Composição apenas: a aba Visão geral reutiliza o cockpit real P1–P5,
 * Documentos e interações reutiliza o painel de evidências P2 e
 * Relatórios e divergências reutiliza a matriz R01–R15. Nenhum dado,
 * indicador ou comportamento de domínio é criado aqui — «—» significa
 * dado ainda não carregado, nunca zero confirmado.
 *
 * Invariantes do rework:
 * - O seletor lista somente competências retornadas pela BFF
 *   (`listCompetences` = existentes e autorizadas); nenhum mês arbitrário.
 * - Resultados são keyed por competência — dados de um período nunca
 *   aparecem sob outro, nem em loading/erro/resposta fora de ordem.
 * - Período e aba vivem na URL canônica
 *   `closing/monthly-closing/{period}?tab=…` — refresh, back/forward e
 *   deep links preservam o contexto.
 * - A aba de documentos só oferece upload quando o contrato P2
 *   (`getCompetence`) confirma que a competência existe — a BFF segue
 *   fail-closed como autoridade final.
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
  getCompetence,
  listCompetences,
  type ClosingCompetence,
} from "../../api/competencesApi";
import {
  getClosingCockpit,
  type Cockpit,
} from "../../api/packagesApi";
import {
  CfQueryErrorBanner,
} from "../../app/cfFeedbackUi";
import {
  FilterSelectField,
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
import { navigatePluginPath } from "../../app/pluginNavigation";
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
  competence_not_found: "Competência não encontrada.",
  not_found: "Competência não encontrada.",
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

function parseTab(search: string): MonthlyClosingTab {
  const value = new URLSearchParams(search).get("tab");
  if (value === "documents" || value === "reports") return value;
  return "overview";
}

function formatPeriod(period: string): string {
  const [year, month] = period.split("-");
  return `${month}/${year}`;
}

function countDivergences(cockpit: Cockpit): number {
  return cockpit.p3.domains.filter(
    (d) =>
      d.divergence !== null && !ZERO_DIVERGENCE_PATTERN.test(d.divergence),
  ).length;
}

function indicatorValue(count: number | null): string {
  return count === null ? "—" : String(count);
}

type CockpitResult =
  | { key: string; kind: "ready"; data: Cockpit; at: Date }
  | { key: string; kind: "error"; error: PanelError };

type CompetencesResult =
  | { key: string; kind: "ready"; data: ClosingCompetence[] }
  | { key: string; kind: "error"; error: PanelError };

/** Caminho canônico preservando competência + aba (RW03). */
function monthlyPath(
  base: string,
  period: string,
  tab: MonthlyClosingTab,
): string {
  const suffix = period && PERIOD_PATTERN.test(period) ? `/${period}` : "";
  const search = tab === "overview" ? "" : `?${TAB_SEARCH[tab]}`;
  return `${base}/closing/monthly-closing${suffix}${search}`;
}

/**
 * Gate P2 da aba Documentos: consulta `getCompetence` separadamente do
 * cockpit. Sem competência existente/autorizada nenhum controle de upload
 * é oferecido — a BFF continua a autoridade final de autorização.
 */
function DocumentsTab({ period }: { period: string }) {
  const [result, setResult] = useState<
    | { key: string; kind: "ready" }
    | { key: string; kind: "error"; error: PanelError }
    | null
  >(null);

  useEffect(() => {
    const controller = new AbortController();
    getCompetence(period, { signal: controller.signal })
      .then((competence) => {
        if (competence && competence.status === "OPEN") {
          setResult({ key: period, kind: "ready" });
        } else {
          setResult({
            key: period,
            kind: "error",
            error: mapError(
              new ApiError(409, "conflict", "competence_not_opened"),
            ),
          });
        }
      })
      .catch((err: unknown) =>
        setResult({ key: period, kind: "error", error: mapError(err) }),
      );
    return () => controller.abort();
  }, [period]);

  const current = result?.key === period ? result : null;

  if (!current) {
    return <p aria-live="polite">Verificando competência…</p>;
  }
  if (current.kind === "error") {
    return (
      <CfEmptyState
        classNames={cfEmptyStateClassNames}
        defaultMessage={`A competência ${formatPeriod(period)} não está aberta ou não está acessível — envio e consulta de evidências indisponíveis.`}
      />
    );
  }
  return <ClosingDocumentsPanel period={period} />;
}

export function MonthlyClosingPage({
  basePath,
  period: routePeriod,
}: {
  basePath: string;
  period?: string;
}) {
  // Período e aba derivam da URL — refresh, back/forward e deep links
  // preservam o contexto (RW03). Sem mês arbitrário como default (RW01).
  const period =
    routePeriod && PERIOD_PATTERN.test(routePeriod) ? routePeriod : "";
  const [, setRouteEpoch] = useState(0);
  const [retryNonce, setRetryNonce] = useState(0);
  const [cockpitResult, setCockpitResult] = useState<CockpitResult | null>(
    null,
  );
  const [listResult, setListResult] = useState<CompetencesResult | null>(
    null,
  );
  const listRequestId = useRef(0);
  const cockpitRequestId = useRef(0);
  const base = normalizeBasePath(basePath);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const sync = () => setRouteEpoch((n) => n + 1);
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  const tab =
    typeof window !== "undefined"
      ? parseTab(window.location.search)
      : "overview";

  const listKey = `list:${retryNonce}`;
  const currentList =
    listResult?.key === listKey ? listResult : null;
  const competences =
    currentList?.kind === "ready" ? currentList.data : null;
  const listError =
    currentList?.kind === "error" ? currentList.error : null;

  // Cockpit keyed por período — nada de mês A sob mês B (RW02).
  const cockpitKey = `cockpit:${period}:${retryNonce}`;
  const currentCockpit =
    period && cockpitResult?.key === cockpitKey ? cockpitResult : null;
  const cockpit =
    currentCockpit?.kind === "ready" ? currentCockpit.data : null;
  const cockpitError =
    currentCockpit?.kind === "error" ? currentCockpit.error : null;
  const cockpitLoading = Boolean(period) && currentCockpit === null;
  const lastUpdated =
    currentCockpit?.kind === "ready" ? currentCockpit.at : null;

  const navigateToPeriod = useCallback(
    (value: string, keepTab: MonthlyClosingTab = tab) => {
      if (!PERIOD_PATTERN.test(value)) return;
      navigatePluginPath(monthlyPath(base, value, keepTab));
    },
    [base, tab],
  );

  const selectTab = useCallback(
    (next: MonthlyClosingTab) => {
      navigatePluginPath(monthlyPath(base, period, next));
    },
    [base, period],
  );

  const retry = useCallback(() => setRetryNonce((n) => n + 1), []);

  // Competências existentes e autorizadas — fonte única do seletor.
  useEffect(() => {
    const id = ++listRequestId.current;
    const controller = new AbortController();
    listCompetences({ signal: controller.signal })
      .then((data) => {
        if (controller.signal.aborted || listRequestId.current !== id) return;
        setListResult({ key: listKey, kind: "ready", data });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || listRequestId.current !== id) return;
        setListResult({ key: listKey, kind: "error", error: mapError(err) });
      });
    return () => controller.abort();
  }, [listKey]);

  useEffect(() => {
    if (!period) return;
    const id = ++cockpitRequestId.current;
    const controller = new AbortController();
    getClosingCockpit(period, controller.signal)
      .then((data) => {
        if (controller.signal.aborted || cockpitRequestId.current !== id) return;
        if (data) {
          setCockpitResult({
            key: cockpitKey,
            kind: "ready",
            data,
            at: new Date(),
          });
        } else {
          setCockpitResult({
            key: cockpitKey,
            kind: "error",
            error: mapError(
              new ApiError(404, "not found", "competence_not_found"),
            ),
          });
        }
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || cockpitRequestId.current !== id) return;
        setCockpitResult({
          key: cockpitKey,
          kind: "error",
          error: mapError(err),
        });
      });
    return () => controller.abort();
  }, [period, cockpitKey]);

  const competenceOptions = useMemo(
    () =>
      (competences ?? [])
        .map((competence) => ({
          value: competence.period,
          label: formatPeriod(competence.period),
        }))
        .sort((a, b) => b.value.localeCompare(a.value)),
    [competences],
  );

  const blockingCount = cockpit?.closing.blocking_reasons.length ?? null;
  const divergenceCount = cockpit ? countDivergences(cockpit) : null;
  // RW04/FM-05C: «Documentos a tratar» não equivale a checklist.EXPECTED —
  // a regra de inclusão dos estados P2 é CONTRACT_TO_INVENTORY no owner P2.
  // Enquanto não houver DTO/owner com a métrica, o cartão mostra «—».
  const documentsCount: number | null = null;

  const competencePicker = (
    <form
      className="cf-settlements-filters"
      onSubmit={(event) => event.preventDefault()}
    >
      <FiltersRow>
        <FilterSelectField
          id="cf-monthly-closing-period"
          label="Competência"
          options={competenceOptions}
          value={period}
          onChange={(value) => navigateToPeriod(value)}
          placeholderOption={
            competences === null
              ? "Carregando competências…"
              : "Selecione uma competência"
          }
          searchable
        />
      </FiltersRow>
    </form>
  );

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
        filters={competencePicker}
        updatedAt={lastUpdated}
        onRefresh={retry}
        refreshing={cockpitLoading}
        onClearFilters={() =>
          navigatePluginPath(monthlyPath(base, "", tab))
        }
      />

      {listError ? (
        <CfQueryErrorBanner
          error={listError}
          dataset="as competências disponíveis"
          onRetry={retry}
        />
      ) : null}

      {period ? (
        <>
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
                  hint: "razões que impedem a conclusão",
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
                  hint: "domínios P3 com divergência",
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
                  hint: "contagem aguardando contrato do owner P2",
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

          <div className="cf-page-stack" aria-busy={cockpitLoading}>
            {cockpitError ? (
              <CfQueryErrorBanner
                error={cockpitError}
                dataset="o fechamento mensal da competência"
                onRetry={retry}
              />
            ) : null}

            {tab === "overview" ? (
              <>
                {cockpitLoading ? (
                  <p aria-live="polite">Carregando visão geral…</p>
                ) : null}
                {!cockpitLoading && !cockpit && !cockpitError ? (
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
                <DocumentsTab period={period} />
                <CfSectionCard title="Checklist da competência">
                  <p>
                    A validação item a item do checklist P2 permanece na página
                    dedicada.
                  </p>
                  <CfActionButton
                    variant="ghost"
                    onClick={() =>
                      navigatePluginPath(
                        `${base}/closing/checklist/${period}`,
                      )
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
                          navigatePluginPath(
                            `${base}/closing/financial-settlements`,
                          )
                        }
                      >
                        Baixas financeiras
                      </CfActionButton>
                    </li>
                    <li>
                      <CfActionButton
                        variant="ghost"
                        onClick={() =>
                          navigatePluginPath(
                            `${base}/closing/stock-inventory`,
                          )
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
        </>
      ) : (
        <div className="cf-page-stack">
          {currentList === null && !listError ? (
            <p aria-live="polite">Carregando competências…</p>
          ) : null}
          {competences && competences.length > 0 ? (
            <CfSectionCard
              title="Competências disponíveis"
              hint={CF_HELP.monthlyClosing.page}
            >
              <ul className="cf-competence-list">
                {competences.map((competence) => (
                  <li key={competence.competence_id}>
                    <button
                      type="button"
                      className="cf-competence-link"
                      onClick={() =>
                        navigateToPeriod(competence.period, "overview")
                      }
                    >
                      {formatPeriod(competence.period)}
                      {competence.item_count !== undefined
                        ? ` · ${competence.item_count} itens`
                        : ""}
                    </button>
                  </li>
                ))}
              </ul>
            </CfSectionCard>
          ) : null}
          {competences && competences.length === 0 ? (
            <CfEmptyState
              classNames={cfEmptyStateClassNames}
              defaultMessage="Nenhuma competência aberta e autorizada para o seu perfil."
            />
          ) : null}
        </div>
      )}
    </section>
  );
}
