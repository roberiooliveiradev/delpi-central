/**
 * Catálogos governados — administração P6 (F1/F5).
 *
 * Consome `/admin/closing-catalogs*` da BFF (MANAGE efetivo — backend
 * é a autoridade). Código de entrada é identidade imutável; edição de
 * rótulo/atributos exige `revision` (OCC); desativação é prospectiva
 * — históricos e pacotes já submetidos nunca são alterados.
 */
import { useCallback, useEffect, useMemo, useState } from "react";

import { ActionButton, ConfirmModalPanel } from "@delpi/plugin-ui/index";

import { ApiError } from "../../api/httpClient";
import {
  createCatalogEntry,
  deactivateCatalogEntry,
  listCatalogs,
  listCatalogEntries,
  reactivateCatalogEntry,
  updateCatalogEntry,
  type CatalogEntry,
  type CatalogKey,
  type CatalogSummary,
} from "../../api/catalogsApi";
import {
  CfFeedbackMessage,
  CfQueryErrorBanner,
  CfSectionLoading,
} from "../../app/cfFeedbackUi";
import {
  CfActionButton,
  CfDialog,
  CfEmptyState,
  CfSectionCard,
  CfStatusBadge,
  CfTitleWithHelp,
  cfConfirmModalClassNames,
  cfEmptyStateClassNames,
} from "../../app/controllershipFinanceUi";
import {
  DataTableSection,
  type DataTableColumn,
} from "../../app/cfDataTableUi";
import { ClosingHero } from "../../app/ClosingHero";
import { CF_HELP } from "../../content/helpTooltips";

type PanelError = { status: number; code: string | null; message: string };

const ERROR_MESSAGES: Record<string, string> = {
  forbidden:
    "Você não tem autorização administrativa (controllership-finance.manage).",
  unauthorized: "Sessão expirada — autentique-se novamente.",
  catalog_not_found: "Catálogo não encontrado.",
  entry_not_found: "Entrada não encontrada neste catálogo.",
  duplicate_entry_code:
    "Já existe uma entrada com este código — o código é a identidade.",
  stale_revision:
    "Entrada alterada por outra sessão — recarregue antes de salvar.",
  entry_inactive: "Entrada inativa — reative antes de editar.",
};

const CATALOG_LABELS: Record<CatalogKey, string> = {
  BANK_ACCOUNT: "Bancos e contas",
  REJECTION_REASON: "Motivos de rejeição",
  ATTACHMENT_ROLE: "Papéis de anexo",
  NOTIFICATION_TARGET: "Destinos de notificação",
  PACKAGE_REQUIRED_AREA: "Áreas obrigatórias por pacote",
  REVIEW_ELIGIBILITY: "Elegibilidade de revisão (Core)",
};

const CATALOG_ORDER: CatalogKey[] = [
  "BANK_ACCOUNT",
  "REJECTION_REASON",
  "ATTACHMENT_ROLE",
  "NOTIFICATION_TARGET",
  "PACKAGE_REQUIRED_AREA",
  "REVIEW_ELIGIBILITY",
];

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

const EMPTY_FORM = { code: "", label: "", attributes: "{}", period: "" };

export function CatalogsAdminPage() {
  const [catalogs, setCatalogs] = useState<CatalogSummary[] | null>(null);
  const [selectedKey, setSelectedKey] = useState<CatalogKey | null>(null);
  const [entries, setEntries] = useState<CatalogEntry[] | null>(null);
  const [error, setError] = useState<PanelError | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null);

  const [entryForm, setEntryForm] = useState(EMPTY_FORM);
  const [editing, setEditing] = useState<CatalogEntry | null>(null);
  const [deactivating, setDeactivating] = useState<CatalogEntry | null>(null);

  const loadCatalogs = useCallback(async () => {
    try {
      setCatalogs(await listCatalogs());
      setUpdatedAt(new Date());
    } catch (err) {
      setError(mapError(err));
    }
  }, []);

  const loadEntries = useCallback(async (key: CatalogKey) => {
    setEntries(null);
    try {
      setEntries(await listCatalogEntries(key));
    } catch (err) {
      setError(mapError(err));
    }
  }, []);

  useEffect(() => {
    void loadCatalogs();
  }, [loadCatalogs]);

  const selectCatalog = useCallback(
    (key: CatalogKey) => {
      setSelectedKey(key);
      setEditing(null);
      setDeactivating(null);
      void loadEntries(key);
    },
    [loadEntries],
  );

  async function run(action: () => Promise<unknown>, okMessage: string) {
    setBusy(true);
    setError(null);
    setFeedback(null);
    try {
      await action();
      setFeedback(okMessage);
      setEditing(null);
      setDeactivating(null);
      setEntryForm(EMPTY_FORM);
      await loadCatalogs();
      if (selectedKey) await loadEntries(selectedKey);
    } catch (err) {
      setError(mapError(err));
    } finally {
      setBusy(false);
    }
  }

  function parseAttributes(): Record<string, unknown> {
    const raw = entryForm.attributes.trim();
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      throw new Error("Atributos devem ser um objeto JSON.");
    }
    return parsed as Record<string, unknown>;
  }

  function submitCreate() {
    if (!selectedKey) return;
    try {
      const attributes = parseAttributes();
      const payload = {
        code: entryForm.code.trim(),
        label: entryForm.label.trim(),
        attributes,
        effective_from_period: entryForm.period.trim() || null,
      };
      void run(
        () => createCatalogEntry(selectedKey, payload),
        "Entrada criada.",
      );
    } catch (err) {
      setError({
        status: 0,
        code: null,
        message:
          err instanceof Error ? err.message : "Atributos inválidos.",
      });
    }
  }

  function submitEdit() {
    if (!selectedKey || !editing) return;
    try {
      const attributes = parseAttributes();
      void run(
        () =>
          updateCatalogEntry(selectedKey, editing.code, {
            label: entryForm.label.trim(),
            attributes,
            revision: editing.revision,
          }),
        "Entrada atualizada.",
      );
    } catch (err) {
      setError({
        status: 0,
        code: null,
        message:
          err instanceof Error ? err.message : "Atributos inválidos.",
      });
    }
  }

  const columns = useMemo<DataTableColumn<CatalogEntry>[]>(
    () => [
      { key: "code", header: "Código", headerHint: CF_HELP.catalogs.columns.code, render: (e) => e.code },
      { key: "label", header: "Rótulo", headerHint: CF_HELP.catalogs.columns.label, render: (e) => e.label },
      {
        key: "attributes",
        header: "Atributos",
        headerHint: CF_HELP.catalogs.columns.attributes,
        render: (e) => (
          <code className="cf-cell-secondary">
            {JSON.stringify(e.attributes)}
          </code>
        ),
      },
      {
        key: "state",
        header: "Estado",
        headerHint: CF_HELP.catalogs.columns.state,
        render: (e) => (
          <CfStatusBadge
            label={e.active ? "Ativa" : "Inativa"}
            variant={e.active ? "success" : "neutral"}
          />
        ),
      },
      {
        key: "revision",
        header: "Revisão",
        headerHint: CF_HELP.catalogs.columns.revision,
        render: (e) => `rev ${e.revision}`,
      },
      {
        key: "actions",
        header: "Ações",
        render: (e) => (
          <div className="cf-pend-actions">
            {e.active ? (
              <>
                <ActionButton
                  type="button"
                  disabled={busy}
                  onClick={() => {
                    setEditing(e);
                    setEntryForm({
                      code: e.code,
                      label: e.label,
                      attributes: JSON.stringify(e.attributes, null, 2),
                      period: e.effective_from_period ?? "",
                    });
                  }}
                >
                  Editar
                </ActionButton>
                <ActionButton
                  type="button"
                  disabled={busy}
                  onClick={() => setDeactivating(e)}
                >
                  Desativar
                </ActionButton>
              </>
            ) : (
              <ActionButton
                type="button"
                disabled={busy}
                onClick={() =>
                  void run(
                    () =>
                      reactivateCatalogEntry(selectedKey!, e.code),
                    "Entrada reativada.",
                  )
                }
              >
                Reativar
              </ActionButton>
            )}
          </div>
        ),
      },
    ],
    [busy, selectedKey],
  );

  const summaryByKey = useMemo(() => {
    const map = new Map<CatalogKey, CatalogSummary>();
    for (const summary of catalogs ?? []) {
      map.set(summary.catalog_key, summary);
    }
    return map;
  }, [catalogs]);

  return (
    <section
      className="cf-page-stack cf-closing-layout"
      aria-label="Catálogos governados"
    >
      <ClosingHero
        title={
          <CfTitleWithHelp
            title="Catálogos governados"
            hint={CF_HELP.catalogs.page}
          />
        }
        subtitle="Configurações de referência da Central de Fechamento — identidade por código, edição versionada e desativação prospectiva."
        filters={null}
        updatedAt={updatedAt}
        onRefresh={() => {
          void loadCatalogs();
          if (selectedKey) void loadEntries(selectedKey);
        }}
        refreshing={busy}
        onClearFilters={() => setSelectedKey(null)}
      />

      <div className="cf-page-stack" aria-busy={busy}>
        {error ? (
          <CfQueryErrorBanner
            error={error}
            dataset="os catálogos"
            onRetry={() => void loadCatalogs()}
          />
        ) : null}
        {feedback ? (
          <CfFeedbackMessage intent="success" title="Ação registrada">
            {feedback}
          </CfFeedbackMessage>
        ) : null}

        <CfSectionCard
          title="Catálogos"
          hint={CF_HELP.catalogs.list}
        >
          {catalogs === null ? (
            <CfSectionLoading label="Carregando catálogos…" variant="panel" />
          ) : (
            <div className="cf-catalog-grid">
              {CATALOG_ORDER.map((key) => {
                const summary = summaryByKey.get(key);
                const active = summary?.active ?? 0;
                const inactive = summary?.inactive ?? 0;
                return (
                  <button
                    key={key}
                    type="button"
                    className={`cf-catalog-card${
                      selectedKey === key ? " cf-catalog-card--active" : ""
                    }`}
                    onClick={() => selectCatalog(key)}
                    aria-pressed={selectedKey === key}
                  >
                    <span className="cf-catalog-card__label">
                      {CATALOG_LABELS[key]}
                    </span>
                    <span className="cf-catalog-card__count">
                      {active} ativa{active === 1 ? "" : "s"}
                      {inactive > 0 ? ` · ${inactive} inativa(s)` : ""}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </CfSectionCard>

        {selectedKey ? (
          <>
            <CfSectionCard
              title={`Entradas — ${CATALOG_LABELS[selectedKey]}`}
              hint={CF_HELP.catalogs.entries}
            >
              <DataTableSection<CatalogEntry>
                title="Entradas do catálogo"
                columns={columns}
                rows={entries ?? []}
                rowKey={(row) => row.entry_id}
                loading={entries === null}
                hideSearch
                emptyMessage="Nenhuma entrada neste catálogo."
              />
            </CfSectionCard>

            <CfSectionCard
              title={editing ? `Editar «${editing.code}»` : "Nova entrada"}
              hint={CF_HELP.catalogs.form}
            >
              <form
                className="cf-catalog-form"
                onSubmit={(event) => {
                  event.preventDefault();
                  if (editing) submitEdit();
                  else submitCreate();
                }}
              >
                <label>
                  Código
                  <input
                    type="text"
                    value={entryForm.code}
                    onChange={(event) =>
                      setEntryForm((f) => ({
                        ...f,
                        code: event.target.value,
                      }))
                    }
                    disabled={busy || editing !== null}
                    required
                    aria-label="Código da entrada"
                  />
                </label>
                <label>
                  Rótulo
                  <input
                    type="text"
                    value={entryForm.label}
                    onChange={(event) =>
                      setEntryForm((f) => ({
                        ...f,
                        label: event.target.value,
                      }))
                    }
                    disabled={busy}
                    required
                    aria-label="Rótulo da entrada"
                  />
                </label>
                <label>
                  Atributos (JSON)
                  <textarea
                    rows={4}
                    value={entryForm.attributes}
                    onChange={(event) =>
                      setEntryForm((f) => ({
                        ...f,
                        attributes: event.target.value,
                      }))
                    }
                    disabled={busy}
                    aria-label="Atributos em JSON"
                  />
                </label>
                {!editing ? (
                  <label>
                    Vigência inicial (AAAA-MM, opcional)
                    <input
                      type="month"
                      value={entryForm.period}
                      onChange={(event) =>
                        setEntryForm((f) => ({
                          ...f,
                          period: event.target.value,
                        }))
                      }
                      disabled={busy}
                      aria-label="Vigência inicial"
                    />
                  </label>
                ) : null}
                <div className="cf-pend-actions">
                  <CfActionButton type="submit" disabled={busy}>
                    {busy
                      ? "Salvando…"
                      : editing
                        ? "Salvar edição"
                        : "Criar entrada"}
                  </CfActionButton>
                  {editing ? (
                    <CfActionButton
                      type="button"
                      variant="ghost"
                      disabled={busy}
                      onClick={() => {
                        setEditing(null);
                        setEntryForm(EMPTY_FORM);
                      }}
                    >
                      Cancelar edição
                    </CfActionButton>
                  ) : null}
                </div>
              </form>
            </CfSectionCard>
          </>
        ) : (
          <CfEmptyState
            classNames={cfEmptyStateClassNames}
            defaultMessage="Selecione um catálogo para ver e administrar as entradas."
          />
        )}
      </div>

      {deactivating ? (
        <CfDialog
          open
          title={`Desativar «${deactivating.code}»`}
          onClose={() => !busy && setDeactivating(null)}
          closeAriaLabel="Fechar desativação"
        >
          <ConfirmModalPanel
            message={
              <>
                Desativar a entrada «{deactivating.code}»? A ação é
                prospectiva — configurações e registros históricos que já
                a referenciam não são alterados.
              </>
            }
            confirmLabel="Desativar entrada"
            cancelLabel="Voltar"
            variant="danger"
            confirmBusy={busy}
            confirmBusyLabel="Desativando…"
            onConfirm={() => {
              if (!selectedKey) return;
              void run(
                () =>
                  deactivateCatalogEntry(
                    selectedKey,
                    deactivating.code,
                    deactivating.revision,
                  ),
                "Entrada desativada prospectivamente.",
              );
            }}
            onCancel={() => setDeactivating(null)}
            classNames={cfConfirmModalClassNames}
          />
        </CfDialog>
      ) : null}
    </section>
  );
}
