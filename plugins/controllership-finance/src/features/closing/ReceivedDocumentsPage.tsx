/**
 * Documentos e interações — experiência do destinatário externo
 * (DRE-019, doc 112 §54; decisão PO: mesma página documental do
 * produto, projeção restrita pela capability
 * `controllership-finance.closing-documents.read`).
 *
 * Três níveis na rota dedicada `closing/documents` (N1→N3 do §54):
 * - `closing/documents` — «Fechamentos recebidos»: entregas correntes
 *   (competência + área destinataria + versão do envio);
 * - `closing/documents/{period}` — entrega da competência: documentos
 *   efetivamente liberados + solicitações do próprio usuário;
 * - `closing/documents/{period}/documents/{id}` — detalhe do documento
 *   (prévia, versões autorizadas, download, conversa e solicitações).
 *
 * Invariantes:
 * - nenhum dado interno é exibido: a página só consome
 *   `/closing/received-documents*` — Visão geral, Relatórios,
 *   Administração e dados operacionais não existem nesta experiência;
 * - resultados são keyed por período/documento — dados de uma
 *   competência nunca aparecem sob outra;
 * - período/documento vivem na URL — F5, back/forward e deep links
 *   preservam o contexto;
 * - a BFF é a autoridade final: esta página nunca decide autorização —
 *   recurso fora do conjunto liberado é 404/erro honesto.
 */
import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { ApiError } from "../../api/httpClient";
import {
  getReceivedDelivery,
  listReceivedDeliveries,
  type ReceivedDelivery,
  type ReceivedDeliveryDetail,
} from "../../api/receivedDocumentsApi";
import {
  CfQueryErrorBanner,
  CfSectionLoading,
} from "../../app/cfFeedbackUi";
import {
  CfActionButton,
  CfEmptyState,
  CfPageHero,
  CfPagePath,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { normalizeBasePath } from "../../app/pluginRoutes";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";
import { ReceivedDocumentDetailPanel } from "./ReceivedDocumentDetailPanel";

type PanelError = { status: number; code: string | null; message: string };

const PERIOD_PATTERN = /^\d{4}-(0[1-9]|1[0-2])$/;

const ERROR_MESSAGES: Record<string, string> = {
  forbidden: "Você não tem autorização para esta consulta.",
  unauthorized: "Sessão expirada — autentique-se novamente.",
  document_not_found:
    "Nenhum fechamento disponibilizado nesta competência.",
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

function formatPeriod(period: string): string {
  const [year, month] = period.split("-");
  return `${month}/${year}`;
}

const AREA_LABELS: Record<string, string> = {
  CONTABIL: "Contabilidade",
  FISCAL: "Fiscal",
};

const REQUEST_STATE_LABELS: Record<string, string> = {
  OPEN: "Aguardando resposta",
  ANSWERED: "Respondida",
  CONFIRMED: "Concluída",
};

const REQUEST_STATE_VARIANTS: Record<
  string,
  "warning" | "info" | "success" | "neutral"
> = {
  OPEN: "warning",
  ANSWERED: "info",
  CONFIRMED: "success",
};

/** Caminho canônico da experiência do destinatário. */
function receivedPath(
  base: string,
  period?: string,
  documentId?: string,
): string {
  let path = `${base}/closing/documents`;
  if (period) path += `/${period}`;
  if (period && documentId)
    path += `/documents/${encodeURIComponent(documentId)}`;
  return path;
}

export function ReceivedDocumentsPage({
  basePath,
  period: routePeriod,
  documentRef,
}: {
  basePath: string;
  period?: string;
  /** UUID do documento na deep route de detalhe. */
  documentRef?: string;
}) {
  const period =
    routePeriod && PERIOD_PATTERN.test(routePeriod) ? routePeriod : "";
  const [, setRouteEpoch] = useState(0);
  const [retryNonce, setRetryNonce] = useState(0);
  const [listResult, setListResult] = useState<{
    key: string;
    deliveries: ReceivedDelivery[];
  } | null>(null);
  const [deliveryResult, setDeliveryResult] = useState<{
    key: string;
    data: ReceivedDeliveryDetail;
  } | null>(null);
  const [error, setError] = useState<{
    key: string;
    error: PanelError;
  } | null>(null);
  const requestId = useRef(0);
  const base = normalizeBasePath(basePath);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const sync = () => setRouteEpoch((n) => n + 1);
    window.addEventListener("popstate", sync);
    return () => window.removeEventListener("popstate", sync);
  }, []);

  const retry = useCallback(() => setRetryNonce((n) => n + 1), []);

  const listKey = `received-list:${retryNonce}`;
  const deliveries =
    listResult?.key === listKey ? listResult.deliveries : null;
  const deliveryKey = `received:${period}:${retryNonce}`;
  const delivery =
    period && deliveryResult?.key === deliveryKey
      ? deliveryResult.data
      : null;
  const currentError =
    (period
      ? error?.key === deliveryKey
      : error?.key === listKey)
      ? error?.error
      : null;

  // N1 — entregas correntes (sem competência na rota).
  useEffect(() => {
    if (period) return;
    const id = ++requestId.current;
    const controller = new AbortController();
    listReceivedDeliveries({ signal: controller.signal })
      .then((items) => {
        if (controller.signal.aborted || requestId.current !== id)
          return;
        setListResult({ key: listKey, deliveries: items });
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id)
          return;
        setError({ key: listKey, error: mapError(err) });
      });
    return () => controller.abort();
  }, [period, listKey]);

  // N2 — entrega da competência (documentos + solicitações próprias).
  useEffect(() => {
    if (!period || documentRef) return;
    const id = ++requestId.current;
    const controller = new AbortController();
    getReceivedDelivery(period, { signal: controller.signal })
      .then((data) => {
        if (controller.signal.aborted || requestId.current !== id)
          return;
        setDeliveryResult({ key: deliveryKey, data });
        setError(null);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id)
          return;
        setError({ key: deliveryKey, error: mapError(err) });
      });
    return () => controller.abort();
  }, [period, documentRef, deliveryKey]);

  const openDelivery = useCallback(
    (deliveryPeriod: string) => {
      navigatePluginPath(receivedPath(base, deliveryPeriod));
    },
    [base],
  );

  const openDocument = useCallback(
    (documentId: string) => {
      navigatePluginPath(receivedPath(base, period, documentId));
    },
    [base, period],
  );

  const backToDelivery = useCallback(() => {
    navigatePluginPath(receivedPath(base, period));
  }, [base, period]);

  const backToList = useCallback(() => {
    navigatePluginPath(receivedPath(base));
  }, [base]);

  const detailMode = Boolean(documentRef && period);

  const pathItems = detailMode
    ? [
        {
          id: "received",
          label: "Documentos e interações",
          href: receivedPath(base),
          onNavigate: (event: { preventDefault: () => void }) => {
            event.preventDefault();
            backToList();
          },
        },
        {
          id: "delivery",
          label: `Fechamento de ${formatPeriod(period)}`,
          href: receivedPath(base, period),
          onNavigate: (event: { preventDefault: () => void }) => {
            event.preventDefault();
            backToDelivery();
          },
        },
      ]
    : period
      ? [
          {
            id: "received",
            label: "Documentos e interações",
            href: receivedPath(base),
            onNavigate: (event: { preventDefault: () => void }) => {
              event.preventDefault();
              backToList();
            },
          },
        ]
      : [];

  const currentLabel = detailMode
    ? "Documento"
    : period
      ? `Fechamento de ${formatPeriod(period)}`
      : "Documentos e interações";

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Documentos e interações"
    >
      <CfPagePath
        ariaLabel="Caminho da página"
        size="sm"
        back={{
          label: "Documentos e interações",
          href: receivedPath(base),
          onNavigate: (event) => {
            event.preventDefault();
            backToList();
          },
        }}
        items={pathItems}
        current={currentLabel}
      />
      <CfPageHero
        eyebrow="Central de Fechamento"
        title={
          <CfTitleWithHelp
            title="Documentos e interações"
            hint={CF_HELP.receivedDocuments.page}
          />
        }
        description={
          period
            ? `Fechamento de ${formatPeriod(period)} — documentos disponibilizados a você.`
            : "Fechamentos disponibilizados a você pela Controladoria."
        }
        actions={
          <CfActionButton
            variant="ghost"
            type="button"
            onClick={retry}
          >
            Atualizar
          </CfActionButton>
        }
      />

      {currentError ? (
        <CfQueryErrorBanner
          error={currentError}
          dataset={
            period ? "a entrega deste fechamento" : "os fechamentos recebidos"
          }
          onRetry={retry}
        />
      ) : null}

      {detailMode ? (
        <ReceivedDocumentDetailPanel
          key={`${period}:${documentRef}`}
          period={period}
          documentId={documentRef ?? ""}
          onBack={backToDelivery}
        />
      ) : period ? (
        <>
          {delivery === null && !currentError ? (
            <CfSectionLoading label="Carregando documentos…" variant="panel" />
          ) : null}

          {delivery ? (
            <>
              <CfSectionCard
                title="Documentos liberados"
                hint={CF_HELP.receivedDocuments.documents}
              >
                <p className="cf-section-subtitle">
                  Documentos efetivamente disponibilizados neste
                  fechamento.
                </p>
                {delivery.deliveries.length > 0 ? (
                  <p className="cf-document-detail__meta">
                    {delivery.deliveries
                      .map(
                        (d) =>
                          `${AREA_LABELS[d.recipient_area] ?? d.recipient_area}` +
                          ` · envio v${d.version_no}` +
                          (d.submitted_at
                            ? ` · ${formatDateTime(d.submitted_at)}`
                            : ""),
                      )
                      .join(" | ")}
                  </p>
                ) : null}
                {delivery.documents.length === 0 ? (
                  <CfEmptyState
                    classNames={cfEmptyStateClassNames}
                    defaultMessage="Nenhum documento liberado neste fechamento ainda."
                  />
                ) : (
                  <ul
                    className="cf-document-cards"
                    aria-label="Documentos liberados"
                  >
                    {delivery.documents.map((doc) => (
                      <li
                        key={doc.document_id}
                        className="cf-document-card"
                      >
                        <div className="cf-document-card__head">
                          <strong>
                            {doc.item_name ??
                              doc.title ??
                              doc.original_name ??
                              "Documento"}
                          </strong>
                          <span className="cf-document-card__badges">
                            <CfStatusBadge
                              variant="info"
                              label="Liberado"
                            />
                          </span>
                        </div>
                        <p className="cf-document-card__meta">
                          {doc.item_name ? "Exigido" : "Documento"}
                          {doc.recipient_area
                            ? ` · ${AREA_LABELS[doc.recipient_area] ?? doc.recipient_area}`
                            : ""}
                          {` · v${doc.version_no}`}
                          {doc.released_at
                            ? ` · ${formatDateTime(doc.released_at)}`
                            : ""}
                        </p>
                        <CfActionButton
                          variant="ghost"
                          onClick={() => openDocument(doc.document_id)}
                        >
                          Ver documento
                        </CfActionButton>
                      </li>
                    ))}
                  </ul>
                )}
              </CfSectionCard>

              <CfSectionCard
                title="Minhas solicitações"
                hint={CF_HELP.receivedDocuments.requestsSummary}
              >
                {delivery.requests.length === 0 ? (
                  <CfEmptyState
                    classNames={cfEmptyStateClassNames}
                    defaultMessage="Nenhuma solicitação registrada neste fechamento."
                  />
                ) : (
                  <ul
                    className="cf-request-list"
                    aria-label="Minhas solicitações"
                  >
                    {delivery.requests.map((request) => (
                      <li key={request.request_id}>
                        <CfStatusBadge
                          variant={
                            REQUEST_STATE_VARIANTS[request.state] ??
                            "neutral"
                          }
                          label={
                            REQUEST_STATE_LABELS[request.state] ??
                            request.state
                          }
                        />{" "}
                        {request.body}
                        <p className="cf-document-detail__meta">
                          {request.created_at
                            ? formatDateTime(request.created_at)
                            : ""}
                        </p>
                        <CfActionButton
                          variant="ghost"
                          onClick={() =>
                            openDocument(request.document_id)
                          }
                        >
                          Abrir documento
                        </CfActionButton>
                      </li>
                    ))}
                  </ul>
                )}
              </CfSectionCard>
            </>
          ) : null}
        </>
      ) : (
        <CfSectionCard
          title="Fechamentos recebidos"
          hint={CF_HELP.receivedDocuments.deliveries}
        >
          {deliveries === null && !currentError ? (
            <CfSectionLoading label="Carregando fechamentos…" variant="panel" />
          ) : null}
          {deliveries && deliveries.length === 0 ? (
            <CfEmptyState
              classNames={cfEmptyStateClassNames}
              defaultMessage="Nenhum fechamento disponibilizado a você ainda."
            />
          ) : null}
          {deliveries && deliveries.length > 0 ? (
            <ul
              className="cf-document-cards"
              aria-label="Fechamentos recebidos"
            >
              {deliveries.map((delivery) => (
                <li
                  key={`${delivery.period}:${delivery.recipient_area}`}
                  className="cf-document-card"
                >
                  <div className="cf-document-card__head">
                    <strong>{formatPeriod(delivery.period)}</strong>
                    <span className="cf-document-card__badges">
                      <CfStatusBadge
                        variant="info"
                        label={
                          AREA_LABELS[delivery.recipient_area] ??
                          delivery.recipient_area
                        }
                      />
                    </span>
                  </div>
                  <p className="cf-document-card__meta">
                    {`${delivery.document_count} documento(s)`}
                    {` · envio v${delivery.version_no}`}
                    {delivery.submitted_at
                      ? ` · ${formatDateTime(delivery.submitted_at)}`
                      : ""}
                  </p>
                  <CfActionButton
                    variant="ghost"
                    onClick={() => openDelivery(delivery.period)}
                  >
                    Ver documentos
                  </CfActionButton>
                </li>
              ))}
            </ul>
          ) : null}
        </CfSectionCard>
      )}
    </section>
  );
}
