import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { FixedPanelPoint } from "@delpi/plugin-ui/index";
import { ArrowLeft, LayoutTemplate, Search, Upload } from "lucide-react";

import {
  applyImportSlideTemplateMdd,
  archiveSlideTemplate,
  cloneSlideTemplate,
  deleteSlideTemplate,
  exportLibrarySlideTemplateMdd,
  listLibrarySlideTemplates,
  previewImportSlideTemplateMdd,
  publishSlideTemplate,
  unpublishSlideTemplate,
  type SlideTemplate,
  type SlideTemplateStatus,
} from "../api/tvDashboardApi";
import { TemplateLibraryContextMenu } from "../components/TemplateLibraryContextMenu";
import { TemplateThumb } from "../components/TemplateThumb";
import { TvDashboardScreenLoading } from "../components/TvDashboardScreenLoading";
import { TvPreviewDetailCard } from "../components/TvPreviewDetailCard";
import { HostContainedDialog } from "../components/ui/Modal";
import { useConfirm } from "../context/ConfirmDialogProvider";
import { TvLibraryPageLayout } from "../layout/TvLibraryPageLayout";
import { TvFilterBarShell, TvNavigationCard, TvPageHeader } from "../layout/tvUi";
import { tvDashboardNotice } from "../utils/tvDashboardNotice";

type Props = {
  canManage: boolean;
  onBack: () => void;
  onOpen: (id: string) => void;
};

type StatusFilter = "" | SlideTemplateStatus | "system" | "custom";

function statusLabel(status: string) {
  if (status === "published") return "Publicado";
  if (status === "archived") return "Arquivado";
  return "Rascunho";
}

/** Biblioteca de templates — mesmo shell da home (TvLibraryPageLayout). */
export function TemplateLibraryPage({ canManage, onBack, onOpen }: Props) {
  const confirm = useConfirm();
  const [items, setItems] = useState<SlideTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<StatusFilter>("");
  const [contextMenu, setContextMenu] = useState<{
    template: SlideTemplate;
    position: FixedPanelPoint;
  } | null>(null);
  const [importPreview, setImportPreview] = useState<{
    file: File;
    label: string;
    description?: string | null;
  } | null>(null);
  const [importBusy, setImportBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    if (!canManage) {
      setLoading(false);
      setItems([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const status =
        filter === "draft" || filter === "published" || filter === "archived"
          ? filter
          : undefined;
      const list = await listLibrarySlideTemplates({
        status,
        q: query,
        isSystem: filter === "system" ? true : filter === "custom" ? false : undefined,
      });
      setItems(list);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar templates.");
      setItems([]);
    } finally {
      setLoading(false);
    }
  }, [canManage, filter, query]);

  useEffect(() => {
    void load();
  }, [load]);

  const emptyHint = useMemo(() => {
    if (!canManage) return "Você não tem permissão para gerenciar a biblioteca de templates.";
    if (query.trim() || filter) return "Nenhum template neste filtro.";
    return "Nenhum template ainda. Importe um .mdd ou salve um slide como template.";
  }, [canManage, filter, query]);

  async function onPickImport(file: File | null) {
    if (!file) return;
    setImportBusy(true);
    try {
      const preview = await previewImportSlideTemplateMdd(file);
      setImportPreview({
        file,
        label: preview.label,
        description: preview.description,
      });
    } catch (err) {
      tvDashboardNotice(err instanceof Error ? err.message : "MDD inválido.");
    } finally {
      setImportBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function confirmImport() {
    if (!importPreview) return;
    setImportBusy(true);
    try {
      const created = await applyImportSlideTemplateMdd(importPreview.file, false);
      setImportPreview(null);
      tvDashboardNotice("Template importado como rascunho.");
      onOpen(created.id);
    } catch (err) {
      tvDashboardNotice(err instanceof Error ? err.message : "Erro ao importar.");
    } finally {
      setImportBusy(false);
    }
  }

  async function runAction(
    item: SlideTemplate,
    action: "publish" | "unpublish" | "archive" | "clone" | "delete" | "export",
  ) {
    try {
      if (action === "export") {
        const blob = await exportLibrarySlideTemplateMdd(item.id);
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${item.key}.mdd`;
        a.click();
        URL.revokeObjectURL(url);
        tvDashboardNotice("MDD exportado.");
        return;
      }
      if (action === "delete") {
        if (item.isSystem) {
          tvDashboardNotice("Templates de sistema não podem ser excluídos.");
          return;
        }
        const ok = await confirm({
          title: "Excluir template",
          message: `Excluir «${item.label}» permanentemente?`,
          confirmLabel: "Excluir",
          variant: "danger",
        });
        if (!ok) return;
        await deleteSlideTemplate(item.id);
        tvDashboardNotice("Template excluído.");
        await load();
        return;
      }
      if (action === "archive") {
        if (item.isSystem) {
          tvDashboardNotice("Templates de sistema não podem ser arquivados.");
          return;
        }
        await archiveSlideTemplate(item.id);
        tvDashboardNotice("Template arquivado.");
        await load();
        return;
      }
      if (action === "publish") {
        await publishSlideTemplate(item.id);
        tvDashboardNotice("Template publicado.");
        await load();
        return;
      }
      if (action === "unpublish") {
        await unpublishSlideTemplate(item.id);
        tvDashboardNotice("Template despublicado.");
        await load();
        return;
      }
      if (action === "clone") {
        const copy = await cloneSlideTemplate(item.id);
        tvDashboardNotice("Cópia criada como rascunho.");
        onOpen(copy.id);
      }
    } catch (err) {
      tvDashboardNotice(err instanceof Error ? err.message : "Falha na ação.");
    }
  }

  if (!canManage) {
    return (
      <TvLibraryPageLayout
        header={
          <TvPageHeader
            eyebrow="Operações · Displays"
            nav={
              <button type="button" className="td-page-back" onClick={onBack}>
                <ArrowLeft size={16} aria-hidden="true" />
                Voltar
              </button>
            }
            title="Biblioteca de templates"
            subtitle="Templates de slide compartilhados na organização."
          />
        }
      >
        <div className="td-library-empty">
          <p>{emptyHint}</p>
        </div>
      </TvLibraryPageLayout>
    );
  }

  return (
    <>
      <TvLibraryPageLayout
        header={
          <TvPageHeader
            eyebrow="Operações · Displays"
            nav={
              <button type="button" className="td-page-back" onClick={onBack}>
                <ArrowLeft size={16} aria-hidden="true" />
                Voltar
              </button>
            }
            title="Biblioteca de templates"
            subtitle="Criar, publicar e importar templates de slide (.mdd) para a organização."
          />
        }
        actions={
          <>
            <TvNavigationCard
              orientation="horizontal"
              icon={<Upload size={22} strokeWidth={2} />}
              title={importBusy ? "Validando…" : "Importar MDD"}
              description="Preview e confirmação antes de gravar como rascunho."
              disabled={importBusy}
              onClick={() => fileRef.current?.click()}
            />
            <input
              ref={fileRef}
              type="file"
              accept=".mdd,application/zip"
              hidden
              onChange={(e) => void onPickImport(e.target.files?.[0] ?? null)}
            />
          </>
        }
        toolbar={
          <TvFilterBarShell ariaLabel="Filtrar templates">
            <div className="td-filter-pills" role="tablist" aria-label="Filtrar templates">
              {(
                [
                  ["", "Todos"],
                  ["published", "Publicados"],
                  ["draft", "Rascunhos"],
                  ["archived", "Arquivados"],
                  ["system", "Sistema"],
                  ["custom", "Custom"],
                ] as const
              ).map(([id, label]) => (
                <button
                  key={id || "all"}
                  type="button"
                  role="tab"
                  aria-selected={filter === id}
                  className={[
                    "td-filter-pill",
                    filter === id ? "td-filter-pill--active" : null,
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() => setFilter(id)}
                >
                  {label}
                </button>
              ))}
            </div>
            <label className="td-library-search">
              <Search size={16} aria-hidden="true" />
              <span className="td-sr-only">Buscar template</span>
              <input
                type="search"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Buscar template"
                autoComplete="off"
              />
            </label>
          </TvFilterBarShell>
        }
      >
        {error ? <div className="td-state">{error}</div> : null}
        {loading ? (
          <TvDashboardScreenLoading label="Carregando templates…" variant="embedded" />
        ) : null}

        {!loading && !error && items.length === 0 ? (
          <div className="td-library-empty">
            <LayoutTemplate size={28} aria-hidden="true" />
            <p>{emptyHint}</p>
            <button
              type="button"
              className="td-btn td-btn--primary"
              onClick={() => fileRef.current?.click()}
            >
              <Upload size={16} aria-hidden="true" />
              Importar MDD
            </button>
          </div>
        ) : null}

        {!loading && !error && items.length > 0 ? (
          <ul className="td-library-grid" aria-label="Templates">
            {items.map((item) => (
              <li
                key={item.id}
                className="td-library-card"
                onContextMenu={(event) => {
                  event.preventDefault();
                  setContextMenu({
                    template: item,
                    position: { x: event.clientX, y: event.clientY },
                  });
                }}
              >
                <TvPreviewDetailCard
                  aria-label={`Abrir ${item.label}`}
                  onClick={() => onOpen(item.id)}
                  media={<TemplateThumb template={item} />}
                  title={item.label}
                  meta={
                    <>
                      <span
                        className={`td-badge ${
                          item.status === "published" ? "td-badge--active" : "td-badge--inactive"
                        }`}
                      >
                        {statusLabel(item.status)}
                        {item.isSystem ? " · Sistema" : ""}
                      </span>
                      {item.description ? <span>{item.description}</span> : null}
                    </>
                  }
                />
              </li>
            ))}
          </ul>
        ) : null}
      </TvLibraryPageLayout>

      {contextMenu ? (
        <TemplateLibraryContextMenu
          open
          position={contextMenu.position}
          template={contextMenu.template}
          onClose={() => setContextMenu(null)}
          onOpen={() => onOpen(contextMenu.template.id)}
          onPublish={() => void runAction(contextMenu.template, "publish")}
          onUnpublish={() => void runAction(contextMenu.template, "unpublish")}
          onClone={() => void runAction(contextMenu.template, "clone")}
          onExport={() => void runAction(contextMenu.template, "export")}
          onArchive={() => void runAction(contextMenu.template, "archive")}
          onDelete={() => void runAction(contextMenu.template, "delete")}
        />
      ) : null}

      <HostContainedDialog
        open={Boolean(importPreview)}
        title="Confirmar importação"
        onClose={() => setImportPreview(null)}
      >
        {importPreview ? (
          <div className="td-save-as-template">
            <p>
              Importar <strong>{importPreview.label}</strong> como rascunho na biblioteca?
            </p>
            {importPreview.description ? <p>{importPreview.description}</p> : null}
            <div className="td-save-as-template__actions">
              <button
                type="button"
                className="td-btn td-btn--ghost"
                onClick={() => setImportPreview(null)}
                disabled={importBusy}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="td-btn td-btn--primary"
                onClick={() => void confirmImport()}
                disabled={importBusy}
              >
                {importBusy ? "Importando…" : "Confirmar"}
              </button>
            </div>
          </div>
        ) : null}
      </HostContainedDialog>
    </>
  );
}
