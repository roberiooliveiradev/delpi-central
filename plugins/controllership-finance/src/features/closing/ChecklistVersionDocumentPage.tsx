/**
 * Documento dentro de uma versão histórica do checklist mestre
 * (UX-015, nível 3 da navegação em cascata): representação read-only
 * do item naquele snapshot — nunca a configuração vigente do catálogo.
 *
 * Separação semântica obrigatória: este item é o registro histórico
 * da versão; alterações prospectivas de exigência acontecem no fluxo
 * governado do catálogo documental (UX-012) via «Editar exigência
 * futura», que navega para `closing/admin/documents/{item_key}` sem
 * tocar a versão histórica. Em DRAFT, a edição do item volta à página
 * da versão (OCC `revision` — mecanismo governado existente).
 */
import { useCallback, useEffect, useRef, useState } from "react";

import {
  getTemplateVersion,
  listChecklistTemplates,
  type ChecklistTemplate,
  type ChecklistTemplateVersionDetail,
} from "../../api/adminApi";
import { CfQueryErrorBanner } from "../../app/cfFeedbackUi";
import {
  CfActionButton,
  CfEmptyState,
  CfPagePath,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  navigatePluginPath,
  navigatePluginView,
} from "../../app/pluginNavigation";
import {
  checklistAdminVersionPath,
} from "../../app/pluginRoutes";
import {
  APPLICABILITY_OPTIONS,
  BRANCH_OPTIONS,
  optionLabel,
  ORIGIN_OPTIONS,
  RECIPIENT_OPTIONS,
  SCOPE_OPTIONS,
  STATUS_LABELS,
  STATUS_VARIANTS,
  toQueryError,
  type QueryError,
} from "./checklistAdminShared";
import { CF_HELP } from "../../content/helpTooltips";
import { formatDateTime } from "../../utils/formatters";

export function ChecklistVersionDocumentPage({
  basePath,
  version,
  itemKey,
}: {
  basePath: string;
  version: number;
  itemKey: string;
}) {
  const [nonce, setNonce] = useState(0);
  const [template, setTemplate] = useState<ChecklistTemplate | null>(
    null,
  );
  const [templateLoaded, setTemplateLoaded] = useState(false);
  const [detail, setDetail] = useState<{
    key: string;
    data: ChecklistTemplateVersionDetail;
  } | null>(null);
  const [error, setError] = useState<QueryError | null>(null);

  const requestId = useRef(0);
  const detailKey = template
    ? `${template.template_id}:${version}:${nonce}`
    : "";
  const detailData = detail?.key === detailKey ? detail.data : null;
  const item =
    detailData?.items.find((entry) => entry.item_key === itemKey) ??
    null;
  const loading = !templateLoaded && !error;

  const reload = useCallback(() => setNonce((n) => n + 1), []);

  const backToVersion = useCallback(
    () =>
      navigatePluginPath(checklistAdminVersionPath(version, basePath)),
    [version, basePath],
  );

  useEffect(() => {
    const id = ++requestId.current;
    const controller = new AbortController();
    listChecklistTemplates({ signal: controller.signal })
      .then((items) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setTemplate(items[0] ?? null);
        setTemplateLoaded(true);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setError(
          toQueryError(err, "Falha ao listar templates de checklist."),
        );
      });
    return () => controller.abort();
  }, [nonce]);

  useEffect(() => {
    if (!template) return;
    const id = ++requestId.current;
    const controller = new AbortController();
    getTemplateVersion(template.template_id, version, {
      signal: controller.signal,
    })
      .then((data) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setDetail({ key: detailKey, data });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted || requestId.current !== id) return;
        setError(toQueryError(err, "Falha ao carregar a versão."));
      });
    return () => controller.abort();
  }, [template, version, detailKey]);

  const openProspectiveEdit = useCallback(() => {
    navigatePluginPath(
      `${basePath}/closing/admin/documents/${encodeURIComponent(itemKey)}`,
    );
  }, [basePath, itemKey]);

  const versionItem = {
    id: "version",
    label: `Versão v${version}`,
    href: checklistAdminVersionPath(version, basePath),
    onNavigate: (event: { preventDefault: () => void }) => {
      event.preventDefault();
      backToVersion();
    },
  };
  const adminItem = {
    id: "admin",
    label: "Administração",
    href: `${basePath}/closing/admin`,
    onNavigate: (event: { preventDefault: () => void }) => {
      event.preventDefault();
      navigatePluginView("checklist_admin", { basePath });
    },
  };

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label={`Documento ${itemKey} na versão v${version}`}
    >
      <CfPagePath
        ariaLabel="Caminho da página"
        size="sm"
        back={{
          label: `Versão v${version}`,
          href: checklistAdminVersionPath(version, basePath),
          onNavigate: (event: { preventDefault: () => void }) => {
            event.preventDefault();
            backToVersion();
          },
        }}
        items={[adminItem, versionItem]}
        current={itemKey}
      />

      <div className="cf-checklist-page__content">
        <div className="cf-lead-stack">
          <CfTitleWithHelp
            title={
              item ? `${item.item_key} — ${item.name}` : itemKey
            }
            hint={CF_HELP.adminVersionDocument.page}
          />
          {detailData ? (
            <p className="cf-validation-panel__doc-detail">
              {`Snapshot da versão v${detailData.version} — ${
                STATUS_LABELS[detailData.status] ?? detailData.status
              }. Representação histórica, somente leitura.`}
            </p>
          ) : null}
        </div>

        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="o documento da versão"
            onRetry={reload}
          />
        ) : null}

        {loading ||
        (templateLoaded && template && !detailData && !error) ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Carregando documento…"
          />
        ) : !error && templateLoaded && !template ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Nenhum template de checklist registrado."
          />
        ) : detailData && !item ? (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage={`O documento ${itemKey} não pertence à versão v${version} do checklist.`}
          />
        ) : detailData && item ? (
          <>
            <CfSectionCard
              title="Identificação"
              hint={CF_HELP.adminVersionDocument.identification}
            >
              <dl className="cf-detail-list">
                <div>
                  <dt>Identificação</dt>
                  <dd>{item.item_key}</dd>
                </div>
                <div>
                  <dt>Nome</dt>
                  <dd>{item.name}</dd>
                </div>
                <div>
                  <dt>Finalidade</dt>
                  <dd>{item.purpose ?? "—"}</dd>
                </div>
                <div>
                  <dt>Orientações</dt>
                  <dd>{item.requirement_notes ?? "—"}</dd>
                </div>
                {item.sort_order !== null ? (
                  <div>
                    <dt>Ordem</dt>
                    <dd>{item.sort_order}</dd>
                  </div>
                ) : null}
              </dl>
            </CfSectionCard>

            <CfSectionCard
              title="Exigência"
              hint={CF_HELP.adminVersionDocument.requirement}
            >
              <dl className="cf-detail-list">
                <div>
                  <dt>Obrigatoriedade</dt>
                  <dd>
                    {optionLabel(
                      APPLICABILITY_OPTIONS,
                      item.applicability,
                    )}
                  </dd>
                </div>
                <div>
                  <dt>Origem</dt>
                  <dd>
                    {optionLabel(ORIGIN_OPTIONS, item.origin_kind)}
                  </dd>
                </div>
                <div>
                  <dt>Destino</dt>
                  <dd>
                    {optionLabel(
                      RECIPIENT_OPTIONS,
                      item.recipient_area,
                    )}
                  </dd>
                </div>
                <div>
                  <dt>Via</dt>
                  <dd>
                    {item.sheet === "FISICO" ? "Físico" : "Eletrônico"}
                  </dd>
                </div>
                <div>
                  <dt>Escopo</dt>
                  <dd>
                    {optionLabel(BRANCH_OPTIONS, item.branch_scope)}
                  </dd>
                </div>
                <div>
                  <dt>Validação</dt>
                  <dd>
                    {optionLabel(SCOPE_OPTIONS, item.validation_scope)}
                  </dd>
                </div>
                <div>
                  <dt>Referência TOTVS</dt>
                  <dd>{item.totvs_report_ref ?? "—"}</dd>
                </div>
              </dl>
            </CfSectionCard>

            <CfSectionCard title="Contexto da versão">
              <div className="cf-card-stack">
                <dl className="cf-detail-list">
                  <div>
                    <dt>Versão</dt>
                    <dd>{`v${detailData.version}`}</dd>
                  </div>
                  <div>
                    <dt>Estado</dt>
                    <dd>
                      <CfStatusBadge
                        label={
                          STATUS_LABELS[detailData.status] ??
                          detailData.status
                        }
                        variant={
                          STATUS_VARIANTS[detailData.status] ??
                          "neutral"
                        }
                      />
                    </dd>
                  </div>
                  <div>
                    <dt>Vigente desde</dt>
                    <dd>{detailData.effective_from_period ?? "—"}</dd>
                  </div>
                  <div>
                    <dt>Publicação</dt>
                    <dd>
                      {detailData.published_at
                        ? formatDateTime(detailData.published_at)
                        : "—"}
                    </dd>
                  </div>
                </dl>
                <div className="cf-validation-panel__item-actions">
                  {detailData.status === "DRAFT" ? (
                    <CfActionButton
                      type="button"
                      variant="ghost"
                      onClick={backToVersion}
                    >
                      Editar item no rascunho
                    </CfActionButton>
                  ) : null}
                  <CfActionButton
                    type="button"
                    onClick={openProspectiveEdit}
                  >
                    Editar exigência futura
                  </CfActionButton>
                </div>
              </div>
            </CfSectionCard>
          </>
        ) : null}
      </div>
    </section>
  );
}
