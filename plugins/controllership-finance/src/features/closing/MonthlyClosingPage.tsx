/**
 * Fechamento mensal — workspace do mês de referência com exatamente três
 * abas (Visão geral / Documentos e interações / Relatórios e divergências),
 * conforme decisão visual do PO no doc 112 §§25–26 e decisão de produto
 * de 26/10/2026 (mês de referência sem abertura formal prévia).
 *
 * Composição apenas: a aba Visão geral reutiliza o cockpit real P1–P5,
 * Documentos e interações reutiliza o painel de evidências P2 e
 * Relatórios e divergências reutiliza a matriz R01–R15. Nenhum dado,
 * indicador ou comportamento de domínio é criado aqui — «—» significa
 * dado ainda não carregado, nunca zero confirmado.
 *
 * Invariantes:
 * - A seleção é por MÊS DE REFERÊNCIA (período YYYY-MM livre), não por
 *   competência formalmente aberta: consultar um mês não executa
 *   `openCompetence` nem exige `monthly_competence`/template publicado.
 * - Resultados são keyed por período — dados de um mês nunca aparecem
 *   sob outro, nem em loading/erro/resposta fora de ordem.
 * - Período e aba vivem na URL canônica
 *   `closing/monthly-closing/{period}?tab=…` — refresh, back/forward e
 *   deep links preservam o contexto.
 * - Contratos atuais P1–P5 seguem ancorados na competência aberta: sem
 *   competência, cada aba exibe estado honesto e a ação autorizada
 *   «Abrir competência» (POST /closing/competences, permission access).
 *   A BFF segue fail-closed como autoridade final de autorização.
 */
import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { ApiError } from "../../api/httpClient";
import {
  getCompetence,
  listCompetences,
  openCompetence,
  type ClosingCompetence,
} from "../../api/competencesApi";
import {
  getClosingCockpit,
  type Cockpit,
} from "../../api/packagesApi";
import {
  CfFeedbackMessage,
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
  no_published_template:
    "Não existe versão publicada vigente do checklist para este mês.",
};

const ZERO_DIVERGENCE_PATTERN = /^-?0+([.,]0+)?$/;

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

/**
 * Estado do contrato de competência para o mês consultado — keyed por
 * período; `not_opened` é resposta legítima de consulta, não erro fatal.
 */
type CompetenceProbe =
  | { key: string; kind: "ready"; data: ClosingCompetence }
  | { key: string; kind: "not_opened" }
  | { key: string; kind: "error"; error: PanelError };

/** Caminho canônico preservando mês de referência + aba. */
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
 * Estado honesto de mês sem competência aberta — a consulta continua
 * possível, mas os painéis derivados do checklist P2 exigem a abertura
 * formal (POST /closing/competences, permission `access`, idempotente).
 */
function NotOpenedNotice({
  period,
  opening,
  openError,
  onOpen,
}: {
  period: string;
  opening: boolean;
  openError: PanelError | null;
  onOpen: () => void;
}) {
  return (
    <>
      <CfEmptyState
        classNames={cfEmptyStateClassNames}
        defaultMessage={`O mês ${formatPeriod(period)} ainda não tem competência aberta.`}
      />
      <CfFeedbackMessage
        intent="info"
        title="Abertura necessária para os dados desta visão"
      >
        Entregáveis, evidências e relatórios desta competência derivam da
        versão publicada do checklist. Abrir a competência cria o snapshot
        do mês — nunca recria uma competência existente.
      </CfFeedbackMessage>
      {openError ? (
        <CfFeedbackMessage
          intent="error"
          title="Falha ao abrir a competência"
        >
          {openError.message}
        </CfFeedbackMessage>
      ) : null}
      <div className="cf-settlements-actions">
        <CfActionButton type="button" onClick={onOpen} disabled={opening}>
          {opening ? "Abrindo…" : "Abrir competência"}
        </CfActionButton>
      </div>
    </>
  );
}

export function MonthlyClosingPage({
  basePath,
  period: routePeriod,
}: {
  basePath: string;
  period?: string;
}) {
  // Período e aba derivam da URL — refresh, back/forward e deep links
  // preservam o contexto. Mês de referência livre, sem default (decisão PO).
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
  const [probeResult, setProbeResult] = useState<CompetenceProbe | null>(
    null,
  );
  const [opening, setOpening] = useState(false);
  const [openError, setOpenError] = useState<{
    key: string;
    error: PanelError;
  } | null>(null);
  const listRequestId = useRef(0);
  const cockpitRequestId = useRef(0);
  const probeRequestId = useRef(0);
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
  const currentList = listResult?.key === listKey ? listResult : null;
  const competences =
    currentList?.kind === "ready" ? currentList.data : null;
  const listError =
    currentList?.kind === "error" ? currentList.error : null;

  // Cockpit keyed por período — nada de mês A sob mês B.
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

  // Probe da competência — autoridade sobre «mês aberto» para os painéis
  // derivados do checklist; não inferir capability do erro do cockpit.
  const probeKey = `probe:${period}:${retryNonce}`;
  const probe =
    period && probeResult?.key === probeKey ? probeResult : null;
  const probeLoading = Boolean(period) && probe === null;
  const openErrorForPeriod =
    openError?.key === period ? openError.error : null;

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

  const openCurrentMonth = useCallback(() => {
    if (!period || opening) return;
    setOpening(true);
    setOpenError(null);
    openCompetence(period)
      .then(() => {
        setOpening(false);
        retry();
      })
      .catch((err: unknown) => {
        setOpening(false);
        setOpenError({ key: period, error: mapError(err) });
      });
  }, [period, opening, retry]);

  // Competências formalmente abertas — lista real de atalhos da landing.
  useEffect(() => {
    const id = ++listRequestId.current;
    const controller = new AbortController();
    listCompetences({ signal: controller.signal })
      .then((data) => {
        if (controller.signal.aborted || listRequestId.current !== id)
          return;
        setListResult({ key: listKey, kind: "ready", data });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || listRequestId.current !== id)
          return;
        setListResult({ key: listKey, kind: "error", error: mapError(err) });
      });
    return () => controller.abort();
  }, [listKey]);

  useEffect(() => {
    if (!period) return;
    const id = ++probeRequestId.current;
    const controller = new AbortController();
    getCompetence(period, { signal: controller.signal })
      .then((data) => {
        if (controller.signal.aborted || probeRequestId.current !== id)
          return;
        setProbeResult({ key: probeKey, kind: "ready", data });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || probeRequestId.current !== id)
          return;
        const error = mapError(err);
        setProbeResult(
          isNotOpened(error)
            ? { key: probeKey, kind: "not_opened" }
            : { key: probeKey, kind: "error", error },
        );
      });
    return () => controller.abort();
  }, [period, probeKey]);

  useEffect(() => {
    if (!period) return;
    const id = ++cockpitRequestId.current;
    const controller = new AbortController();
    getClosingCockpit(period, controller.signal)
      .then((data) => {
        if (controller.signal.aborted || cockpitRequestId.current !== id)
          return;
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
        if (controller.signal.aborted || cockpitRequestId.current !== id)
          return;
        setCockpitResult({
          key: cockpitKey,
          kind: "error",
          error: mapError(err),
        });
      });
    return () => controller.abort();
  }, [period, cockpitKey]);

  const blockingCount = cockpit?.closing.blocking_reasons.length ?? null;
  const divergenceCount = cockpit ? countDivergences(cockpit) : null;
  // «Documentos a tratar» não equivale a checklist.EXPECTED — a regra de
  // inclusão dos estados P2 é CONTRACT_TO_INVENTORY no owner P2 (FM-05C).
  // Enquanto não houver DTO/owner com a métrica, o cartão mostra «—».
  const documentsCount: number | null = null;

  const referencePicker = (
    <form
      className="cf-settlements-filters"
      onSubmit={(event) => event.preventDefault()}
    >
      <FiltersRow>
        <FilterInputField
          id="cf-monthly-closing-period"
          label="Mês de referência"
          type="month"
          value={period}
          onChange={(value) => navigateToPeriod(value)}
        />
      </FiltersRow>
    </form>
  );

  const renderProbeGate = (children: React.ReactNode) => {
    if (probeLoading) {
      return <p aria-live="polite">Verificando competência…</p>;
    }
    if (probe?.kind === "not_opened") {
      return (
        <NotOpenedNotice
          period={period}
          opening={opening}
          openError={openErrorForPeriod}
          onOpen={openCurrentMonth}
        />
      );
    }
    if (probe?.kind === "error") {
      return (
        <CfQueryErrorBanner
          error={probe.error}
          dataset="a competência do mês"
          onRetry={retry}
        />
      );
    }
    if (probe?.kind === "ready" && probe.data.status !== "OPEN") {
      return (
        <CfEmptyState
          classNames={cfEmptyStateClassNames}
          defaultMessage={`A competência ${formatPeriod(period)} não está aberta para esta operação.`}
        />
      );
    }
    return children;
  };

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
        subtitle="Bancada de trabalho do mês de referência: visão geral, documentos e relatórios do fechamento."
        filters={referencePicker}
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
          dataset="as competências abertas"
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
            {cockpitError && !isNotOpened(cockpitError) ? (
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
                {!cockpitLoading &&
                cockpitError &&
                isNotOpened(cockpitError) ? (
                  <NotOpenedNotice
                    period={period}
                    opening={opening}
                    openError={openErrorForPeriod}
                    onOpen={openCurrentMonth}
                  />
                ) : null}
                {!cockpitLoading && !cockpit && !cockpitError ? (
                  <CfEmptyState
                    classNames={cfEmptyStateClassNames}
                    defaultMessage="Sem dados de fechamento para o mês de referência."
                  />
                ) : null}
                {cockpit ? <CockpitSummaryPanel cockpit={cockpit} /> : null}
              </>
            ) : null}

            {tab === "documents" ? (
              <>
                {renderProbeGate(<ClosingDocumentsPanel period={period} />)}
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
                {renderProbeGate(<ReportsMatrixPanel period={period} />)}
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
              title="Competências abertas"
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
              defaultMessage="Nenhuma competência aberta ainda — selecione um mês de referência para consultar."
            />
          ) : null}
        </div>
      )}
    </section>
  );
}
