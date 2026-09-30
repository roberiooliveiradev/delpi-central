import { useCallback, useEffect, useState } from "react";

import {
  ActionButton,
  ContextMenu,
  ContextMenuDivider,
  ContextMenuItem,
  IconButton,
  ScreenLoading,
  SegmentToggle,
  type FixedPanelPoint,
} from "@delpi/plugin-ui/index";
import {
  Archive,
  ArchiveRestore,
  Copy,
  Download,
  FilePlus2,
  FolderOpen,
  MoreVertical,
  Upload,
} from "lucide-react";

import {
  archiveModel,
  BpmnModelerApiError,
  createModel,
  duplicateModel,
  exportWorkingCopy,
  listModels,
  unarchiveModel,
  type ModelListPage,
  type ModelSummary,
} from "../data/api/bpmnModelerApi";
import type { Capabilities } from "../state/capabilities";
import { CreateModelDialog } from "../components/CreateModelDialog";
import { ImportDialog } from "../components/ImportDialog";
import { HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  BPMNM_ROOT_CLASS,
  BpmnmDataCardsGrid,
  BpmnmDataRecordCard,
  BpmnmEmptyState,
  BpmnmFilters,
  BpmnmModal,
  BpmnmPageHero,
  BpmnmStateBanner,
  BpmnmStatusBadge,
  BpmnmTextField,
} from "../ui/kit";

type Props = {
  getAccessToken?: () => string | undefined;
  capabilities: Capabilities;
  navigate: (path: string) => void;
};

type ArchivedFilter = "active" | "archived" | "all";

type SortValue = "updated_at:desc" | "updated_at:asc" | "created_at:desc" | "display_name:asc";

const SORT_OPTIONS: readonly { value: SortValue; label: string }[] = [
  { value: "updated_at:desc", label: "Atualização recente" },
  { value: "updated_at:asc", label: "Atualização antiga" },
  { value: "created_at:desc", label: "Criação recente" },
  { value: "display_name:asc", label: "Nome A–Z" },
];

const STATUS_OPTIONS = [
  { value: "active", label: "Ativos" },
  { value: "archived", label: "Arquivados" },
  { value: "all", label: "Todos" },
] as const;

function downloadBpmn(filename: string, xml: string) {
  const blob = new Blob([xml], { type: "application/xml" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/** Model Library (P4 §18) — cards, busca, filtro de arquivados, paginação. */
export function ModelLibraryPage({ getAccessToken, capabilities, navigate }: Props) {
  const [page, setPage] = useState<ModelListPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [archived, setArchived] = useState<ArchivedFilter>("active");
  const [sortValue, setSortValue] = useState<SortValue>("updated_at:desc");
  const [pageNumber, setPageNumber] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [menu, setMenu] = useState<{ model: ModelSummary; position: FixedPanelPoint } | null>(null);
  const [duplicateTarget, setDuplicateTarget] = useState<ModelSummary | null>(null);
  const [duplicateName, setDuplicateName] = useState("");

  const [sort, direction] = sortValue.split(":") as ["updated_at" | "created_at" | "display_name", "asc" | "desc"];

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await listModels({
        query: query || undefined,
        archived,
        sort,
        direction,
        page: pageNumber,
        page_size: 25,
        getAccessToken,
      });
      setPage(result);
    } catch (err) {
      setError(
        err instanceof BpmnModelerApiError
          ? err.message
          : "Falha ao carregar modelos.",
      );
    } finally {
      setLoading(false);
    }
  }, [query, archived, sort, direction, pageNumber, getAccessToken]);

  useEffect(() => {
    void Promise.resolve().then(load);
  }, [load]);

  const onCreate = async (name: string) => {
    setBusy(true);
    try {
      const outcome = await createModel(name, { getAccessToken });
      navigate(`/apps/bpmn-modeler/models/${outcome.model_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao criar modelo.");
      setCreateOpen(false);
    } finally {
      setBusy(false);
    }
  };

  const onArchive = async (model: ModelSummary) => {
    try {
      if (model.archived_at) {
        await unarchiveModel(model.id, model.version, { getAccessToken });
      } else {
        await archiveModel(model.id, model.version, { getAccessToken });
      }
      void load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao arquivar.");
    }
  };

  const onDuplicate = async (model: ModelSummary, name: string) => {
    setBusy(true);
    try {
      const outcome = await duplicateModel(model.id, name, { getAccessToken });
      setDuplicateTarget(null);
      navigate(`/apps/bpmn-modeler/models/${outcome.model_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao duplicar.");
    } finally {
      setBusy(false);
    }
  };

  const onExport = async (model: ModelSummary) => {
    try {
      const xml = await exportWorkingCopy(model.id, { getAccessToken });
      downloadBpmn(`${model.display_name || model.id}.bpmn`, xml);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao exportar.");
    }
  };

  const openModelPath = (id: string) => `/apps/bpmn-modeler/models/${id}`;

  return (
    <div className={`${BPMNM_ROOT_CLASS} dashboard-page bpmnm-page bpmnm-library`}>
      <BpmnmPageHero
        eyebrow="Processos"
        title="Meu Modelador de Processos"
        description="Crie, organize e mantenha os processos da DELPI em BPMN."
        actions={
          capabilities.edit ? (
            <>
              <ActionButton
                type="button"
                variant="primary"
                title={HELP_TOOLTIPS.library.create}
                onClick={() => setCreateOpen(true)}
              >
                <FilePlus2 size={16} aria-hidden="true" /> Novo modelo
              </ActionButton>
              <ActionButton
                type="button"
                title={HELP_TOOLTIPS.library.import}
                onClick={() => setImportOpen(true)}
              >
                <Upload size={16} aria-hidden="true" /> Importar BPMN
              </ActionButton>
            </>
          ) : undefined
        }
      />

      <BpmnmFilters.FiltersRow>
        <SegmentToggle
          options={STATUS_OPTIONS}
          value={archived}
          onChange={(value) => {
            setArchived(value as ArchivedFilter);
            setPageNumber(1);
          }}
          ariaLabel="Filtrar por estado"
          prefix="bpmnm"
        />
        <BpmnmFilters.FilterInputField
          label="Buscar modelos"
          type="search"
          value={query}
          placeholder="Buscar modelo…"
          onChange={(value) => {
            setQuery(value);
            setPageNumber(1);
          }}
        />
        <BpmnmFilters.FilterSelectField
          label="Ordenar por"
          value={sortValue}
          options={SORT_OPTIONS}
          onChange={(value) => {
            setSortValue(value as SortValue);
            setPageNumber(1);
          }}
        />
      </BpmnmFilters.FiltersRow>

      {error ? (
        <BpmnmStateBanner variant="error" className="bpmnm-error">
          {error}{" "}
          <ActionButton variant="link" onClick={() => void load()}>
            Tentar novamente
          </ActionButton>
        </BpmnmStateBanner>
      ) : null}

      {loading ? (
        <ScreenLoading variant="embedded" label="Carregando modelos…" />
      ) : page && page.items.length === 0 ? (
        <BpmnmEmptyState
          title={query ? "Sem resultados" : "Nenhum modelo"}
          message={
            query
              ? "Nenhum resultado para a busca."
              : "Nenhum modelo ainda — crie ou importe um arquivo .bpmn."
          }
        >
          {capabilities.edit && !query ? (
            <ActionButton variant="primary" onClick={() => setCreateOpen(true)}>
              Criar primeiro modelo
            </ActionButton>
          ) : null}
        </BpmnmEmptyState>
      ) : (
        <BpmnmDataCardsGrid ariaLabel="Modelos de processo">
          {(page?.items ?? []).map((model) => (
            <BpmnmDataRecordCard
              key={model.id}
              href={openModelPath(model.id)}
              onNavigate={(event) => {
                event.preventDefault();
                navigate(openModelPath(model.id));
              }}
              title={model.display_name}
              subtitle={`Atualizado em ${new Date(model.updated_at).toLocaleString("pt-BR")}`}
              status={
                <BpmnmStatusBadge
                  label={model.archived_at ? "Arquivado" : "Ativo"}
                  variant={model.archived_at ? "neutral" : "success"}
                />
              }
              fields={[
                { id: "revisions", label: "Revisões", value: model.revision_count },
                { id: "created", label: "Criado em", value: new Date(model.created_at).toLocaleDateString("pt-BR") },
              ]}
              context={
                <div
                  className="bpmnm-card-menu-anchor"
                  title={HELP_TOOLTIPS.library.actions}
                  onClick={(event) => {
                    const rect =
                      event.currentTarget.getBoundingClientRect();
                    setMenu((m) =>
                      m?.model.id === model.id
                        ? null
                        : {
                            model,
                            position: { x: rect.right, y: rect.bottom },
                          },
                    );
                  }}
                >
                  <IconButton aria-label={`Ações de ${model.display_name}`}>
                    <MoreVertical size={16} aria-hidden="true" />
                  </IconButton>
                </div>
              }
            />
          ))}
        </BpmnmDataCardsGrid>
      )}

      {page && (page.page > 1 || page.has_more) ? (
        <nav className="bpmnm-pagination" aria-label="Paginação">
          <ActionButton
            type="button"
            disabled={pageNumber <= 1}
            onClick={() => setPageNumber((p) => p - 1)}
          >
            Anterior
          </ActionButton>
          <span>Página {pageNumber}</span>
          <ActionButton
            type="button"
            disabled={!page.has_more}
            onClick={() => setPageNumber((p) => p + 1)}
          >
            Próxima
          </ActionButton>
        </nav>
      ) : null}

      <ContextMenu
        open={menu !== null}
        position={menu?.position ?? null}
        onClose={() => setMenu(null)}
        aria-label="Ações do modelo"
        portalScopeClassName={BPMNM_ROOT_CLASS}
      >
        {menu ? (
          <>
            <ContextMenuItem
              label="Abrir"
              icon={FolderOpen}
              onSelect={() => {
                setMenu(null);
                navigate(openModelPath(menu.model.id));
              }}
            />
            <ContextMenuItem
              label="Exportar BPMN"
              icon={Download}
              onSelect={() => {
                setMenu(null);
                void onExport(menu.model);
              }}
            />
            {capabilities.manage ? (
              <>
                <ContextMenuItem
                  label="Duplicar"
                  icon={Copy}
                  onSelect={() => {
                    setDuplicateName(`${menu.model.display_name} (cópia)`);
                    setDuplicateTarget(menu.model);
                    setMenu(null);
                  }}
                />
                <ContextMenuDivider />
                <ContextMenuItem
                  label={menu.model.archived_at ? "Desarquivar" : "Arquivar"}
                  icon={menu.model.archived_at ? ArchiveRestore : Archive}
                  onSelect={() => {
                    setMenu(null);
                    void onArchive(menu.model);
                  }}
                />
              </>
            ) : null}
          </>
        ) : null}
      </ContextMenu>

      <CreateModelDialog
        open={createOpen}
        busy={busy}
        onCancel={() => setCreateOpen(false)}
        onConfirm={(name) => void onCreate(name)}
      />
      <ImportDialog
        open={importOpen}
        getAccessToken={getAccessToken}
        onCancel={() => setImportOpen(false)}
        onImported={(modelId) => navigate(`/apps/bpmn-modeler/models/${modelId}`)}
      />

      <BpmnmModal
        open={duplicateTarget !== null}
        title="Duplicar modelo"
        onClose={() => setDuplicateTarget(null)}
        initialFocusSelector="input"
      >
        <form
          onSubmit={(event) => {
            event.preventDefault();
            const name = duplicateName.trim();
            if (duplicateTarget && name) void onDuplicate(duplicateTarget, name);
          }}
        >
          <BpmnmTextField
            label="Nome da cópia"
            value={duplicateName}
            onChange={setDuplicateName}
            required
          />
          <div className="bpmnm-dialog__actions">
            <ActionButton
              type="button"
              onClick={() => setDuplicateTarget(null)}
              disabled={busy}
            >
              Cancelar
            </ActionButton>
            <ActionButton
              variant="primary"
              type="submit"
              disabled={duplicateName.trim().length === 0 || busy}
            >
              {busy ? "Duplicando…" : "Duplicar"}
            </ActionButton>
          </div>
        </form>
      </BpmnmModal>
    </div>
  );
}
