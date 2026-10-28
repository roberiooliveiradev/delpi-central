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
  hintedLabel,
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
        <div className="cf-lead-row">
          <div className="cf-lead-stack">
            <div className="cf-lead-badges">
              <CfTitleWithHelp
                title={item ? item.name : itemKey}
                hint={CF_HELP.adminVersionDocument.page}
              />
              {item ? (
                <>
                  <CfStatusBadge
                    label={optionLabel(
                      APPLICABILITY_OPTIONS,
                      item.applicability,
                    )}
                    variant="neutral"
                  />
                  <CfStatusBadge
                    label={
                      item.sheet === "FISICO" ? "Físico" : "Eletrônico"
                    }
                    variant="neutral"
                  />
                </>
              ) : null}
              {detailData ? (
                <CfStatusBadge
                  label={
                    STATUS_LABELS[detailData.status] ??
                    detailData.status
                  }
                  variant={
                    STATUS_VARIANTS[detailData.status] ?? "neutral"
                  }
                />
              ) : null}
            </div>
            {detailData ? (
              <p className="cf-validation-panel__doc-detail">
                {`Snapshot histórico da versão v${detailData.version} — somente leitura. Alterações de exigência são sempre prospectivas.`}
              </p>
            ) : null}
          </div>
          {detailData && item ? (
            <div className="cf-validation-panel__item-actions">
              <CfActionButton
                type="button"
                variant="ghost"
                onClick={backToVersion}
              >
                Voltar à versão
              </CfActionButton>
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
                  <dt>{hintedLabel("Nome", CF_HELP.adminVersionDocument.fields.name)}</dt>
                  <dd>{item.name}</dd>
                </div>
                <div>
                  <dt>{hintedLabel("Identificador", CF_HELP.adminVersionDocument.fields.identifier)}</dt>
                  <dd>{item.item_key}</dd>
                </div>
                <div className="cf-detail-list__full">
                  <dt>{hintedLabel("Finalidade", CF_HELP.adminVersionDocument.fields.purpose)}</dt>
                  <dd>{item.purpose ?? "Não informada"}</dd>
                </div>
                <div className="cf-detail-list__full">
                  <dt>{hintedLabel("Orientações", CF_HELP.adminVersionDocument.fields.notes)}</dt>
                  <dd>{item.requirement_notes ?? "Não informadas"}</dd>
                </div>
                {item.sort_order !== null ? (
                  <div>
                    <dt>{hintedLabel("Ordem", CF_HELP.adminVersionDocument.fields.order)}</dt>
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
                  <dt>{hintedLabel("Obrigatoriedade", CF_HELP.adminVersionDocument.fields.applicability)}</dt>
                  <dd>
                    {optionLabel(
                      APPLICABILITY_OPTIONS,
                      item.applicability,
                    )}
                  </dd>
                </div>
                <div>
                  <dt>{hintedLabel("Origem", CF_HELP.adminVersionDocument.fields.origin)}</dt>
                  <dd>
                    {optionLabel(ORIGIN_OPTIONS, item.origin_kind)}
                  </dd>
                </div>
                <div>
                  <dt>{hintedLabel("Destino", CF_HELP.adminVersionDocument.fields.recipient)}</dt>
                  <dd>
                    {optionLabel(
                      RECIPIENT_OPTIONS,
                      item.recipient_area,
                    )}
                  </dd>
                </div>
                <div>
                  <dt>{hintedLabel("Via", CF_HELP.adminVersionDocument.fields.sheet)}</dt>
                  <dd>
                    {item.sheet === "FISICO" ? "Físico" : "Eletrônico"}
                  </dd>
                </div>
                <div>
                  <dt>{hintedLabel("Escopo", CF_HELP.adminVersionDocument.fields.scope)}</dt>
                  <dd>
                    {optionLabel(BRANCH_OPTIONS, item.branch_scope)}
                  </dd>
                </div>
                <div>
                  <dt>{hintedLabel("Validação", CF_HELP.adminVersionDocument.fields.validation)}</dt>
                  <dd>
                    {optionLabel(SCOPE_OPTIONS, item.validation_scope)}
                  </dd>
                </div>
                <div className="cf-detail-list__full">
                  <dt>{hintedLabel("Referência TOTVS", CF_HELP.adminVersionDocument.fields.totvsRef)}</dt>
                  <dd>{item.totvs_report_ref ?? "Não informada"}</dd>
                </div>
              </dl>
            </CfSectionCard>

            <p className="cf-version-context">
              <span>{`Versão v${detailData.version}`}</span>
              <CfStatusBadge
                label={
                  STATUS_LABELS[detailData.status] ?? detailData.status
                }
                variant={
                  STATUS_VARIANTS[detailData.status] ?? "neutral"
                }
              />
              <span>{`Vigente desde ${detailData.effective_from_period ?? "—"}`}</span>
              {detailData.published_at ? (
                <span>{`Publicada em ${formatDateTime(detailData.published_at)}`}</span>
              ) : null}
            </p>
          </>
        ) : null}
      </div>
    </section>
  );
}
