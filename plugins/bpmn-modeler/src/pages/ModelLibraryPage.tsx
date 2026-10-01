import { useCallback, useEffect, useRef, useState } from "react";

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
import { BpmnModelThumb } from "../components/BpmnModelThumb";
import { CreateModelDialog } from "../components/CreateModelDialog";
import { ImportDialog } from "../components/ImportDialog";
import { HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  BPMNM_ROOT_CLASS,
  BpmnmEmptyState,
  BpmnmFilterBarShell,
  BpmnmFilters,
  BpmnmModal,
  BpmnmNavigationCard,
  BpmnmPageHeader,
  BpmnmCompactPagination,
  BpmnmPreviewDetailCard,
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

function formatUpdatedAt(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  const now = new Date();
  const sameDay = date.toDateString() === now.toDateString();
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  const time = date.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  if (sameDay) return `hoje, ${time}`;
  if (date.toDateString() === yesterday.toDateString()) return `ontem, ${time}`;
  return date.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

function revisionLabel(count: number | null | undefined): string {
  const n = count ?? 0;
  return n === 1 ? "1 revisão" : `${n} revisões`;
}

/** Model Library (P4 §18) — padrão visual do TV Dashboard (header leve,
 *  action cards, toolbar compacta, grid com preview BPMN derivado). */
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
  const longPress = useRef<{ timer: number; x: number; y: number } | null>(null);
  const suppressClick = useRef(false);

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

  useEffect(
    () => () => {
      if (longPress.current !== null) window.clearTimeout(longPress.current.timer);
    },
    [],
  );

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

  const openModelMenu = (model: ModelSummary, position: FixedPanelPoint) => {
    setMenu({ model, position });
  };

  const cancelLongPress = () => {
    if (longPress.current !== null) {
      window.clearTimeout(longPress.current.timer);
      longPress.current = null;
    }
  };

  /** Touch/coarse pointer: press-and-hold ~520ms abre o mesmo menu contextual.
   *  Tap simples abre o modelo; scroll/movimento cancela sem abrir nada. */
  const onCardPointerDown = (model: ModelSummary, event: React.PointerEvent) => {
    suppressClick.current = false;
    if (event.pointerType !== "touch" && event.pointerType !== "pen") return;
    cancelLongPress();
    const { clientX, clientY } = event;
    longPress.current = {
      x: clientX,
      y: clientY,
      timer: window.setTimeout(() => {
        longPress.current = null;
        suppressClick.current = true;
        openModelMenu(model, { x: clientX, y: clientY });
      }, 520),
    };
  };

  const onCardPointerMove = (event: React.PointerEvent) => {
    const lp = longPress.current;
    if (!lp) return;
    if (Math.hypot(event.clientX - lp.x, event.clientY - lp.y) > 10) {
      cancelLongPress();
    }
  };

  const cardMenuButton = (model: ModelSummary) => (
    <span
      className="bpmnm-model-card__menu"
      title={HELP_TOOLTIPS.library.actions}
      onClick={(event) => {
        event.stopPropagation();
        const rect = event.currentTarget.getBoundingClientRect();
        setMenu((m) =>
          m?.model.id === model.id
            ? null
            : { model, position: { x: rect.right, y: rect.bottom } },
        );
      }}
    >
      <IconButton aria-label={`Ações de ${model.display_name}`}>
        <MoreVertical size={16} aria-hidden="true" />
      </IconButton>
    </span>
  );

  return (
    <div className={`${BPMNM_ROOT_CLASS} dashboard-page bpmnm-page bpmnm-library`}>
      <BpmnmPageHeader
        eyebrow="Processos · BPMN"
        title="Meu Modelador de Processos"
        subtitle="Crie, organize e mantenha os processos da DELPI em BPMN."
      />

      {capabilities.edit ? (
        <div className="bpmnm-action-grid">
          <BpmnmNavigationCard
            icon={<FilePlus2 size={22} strokeWidth={2} aria-hidden="true" />}
            title="Novo modelo"
            description="Crie um processo BPMN do zero."
            onClick={() => setCreateOpen(true)}
            aria-label={HELP_TOOLTIPS.library.create}
          />
          <BpmnmNavigationCard
            icon={<Upload size={22} strokeWidth={2} aria-hidden="true" />}
            title="Importar BPMN"
            description="Abra um arquivo .bpmn existente."
            onClick={() => setImportOpen(true)}
            aria-label={HELP_TOOLTIPS.library.import}
          />
        </div>
      ) : null}

      <BpmnmFilterBarShell className="bpmnm-library-toolbar" ariaLabel="Filtrar modelos">
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
      </BpmnmFilterBarShell>

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
          title={query ? "Sem resultados" : "Nenhum modelo ativo"}
          message={
            query
              ? "Nenhum resultado para a busca."
              : "Crie seu primeiro modelo BPMN ou importe um arquivo existente."
          }
        >
          {capabilities.edit && !query ? (
            <ActionButton variant="primary" onClick={() => setCreateOpen(true)}>
              Criar primeiro modelo
            </ActionButton>
          ) : null}
        </BpmnmEmptyState>
      ) : (
        <ul className="bpmnm-library-grid" aria-label="Modelos de processo">
          {(page?.items ?? []).map((model) => (
            <li
              key={model.id}
              className={`bpmnm-model-card${menu?.model.id === model.id ? " is-menu-open" : ""}`}
              onPointerDown={(event) => onCardPointerDown(model, event)}
              onPointerMove={onCardPointerMove}
              onPointerUp={cancelLongPress}
              onPointerCancel={cancelLongPress}
              onKeyDown={(event) => {
                if (
                  event.key === "ContextMenu" ||
                  (event.shiftKey && event.key === "F10")
                ) {
                  event.preventDefault();
                  const rect = event.currentTarget.getBoundingClientRect();
                  openModelMenu(model, { x: rect.right - 16, y: rect.bottom - 16 });
                }
              }}
            >
              <BpmnmPreviewDetailCard
                aria-label={`Abrir ${model.display_name}`}
                media={
                  <BpmnModelThumb
                    modelId={model.id}
                    version={model.version}
                    getAccessToken={getAccessToken}
                  />
                }
                title={model.display_name}
                meta={
                  <>
                    <BpmnmStatusBadge
                      label={model.archived_at ? "Arquivado" : "Ativo"}
                      variant={model.archived_at ? "neutral" : "success"}
                    />
                    <span className="bpmnm-card-meta-line">
                      {revisionLabel(model.latest_revision_number)}
                      {" · "}
                      Atualizado {formatUpdatedAt(model.updated_at)}
                    </span>
                  </>
                }
                onClick={() => {
                  if (suppressClick.current) {
                    suppressClick.current = false;
                    return;
                  }
                  navigate(openModelPath(model.id));
                }}
                onContextMenu={(event) => {
                  event.preventDefault();
                  cancelLongPress();
                  openModelMenu(model, { x: event.clientX, y: event.clientY });
                }}
              />
              {cardMenuButton(model)}
            </li>
          ))}
        </ul>
      )}

      {page && (page.page > 1 || page.has_more) ? (
        <BpmnmCompactPagination
          page={pageNumber}
          pageSize={page.page_size}
          total={page.page_size * pageNumber + (page.has_more ? 1 : 0)}
          totalPages={pageNumber + (page.has_more ? 1 : 0)}
          onPageChange={setPageNumber}
        />
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
            {capabilities.manage ? (
              <ContextMenuItem
                label="Duplicar"
                icon={Copy}
                onSelect={() => {
                  setDuplicateName(`${menu.model.display_name} (cópia)`);
                  setDuplicateTarget(menu.model);
                  setMenu(null);
                }}
              />
            ) : null}
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
