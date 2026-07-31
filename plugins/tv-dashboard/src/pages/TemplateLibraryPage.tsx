import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
import { TemplateThumb } from "../components/TemplateThumb";
import { HostContainedDialog } from "../components/ui/Modal";
import { useConfirm } from "../context/ConfirmDialogProvider";
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

export function TemplateLibraryPage({ canManage, onBack, onOpen }: Props) {
  const confirm = useConfirm();
  const [items, setItems] = useState<SlideTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<StatusFilter>("");
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
    return "Nenhum template ainda. Importe um .mdd ou crie a partir de um slide.";
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
      <div className="td-home">
        <section className="td-home__greeting">
          <button type="button" className="td-btn td-btn--ghost" onClick={onBack}>
            <ArrowLeft size={16} aria-hidden="true" /> Voltar
          </button>
          <h2 className="td-home__hello">Biblioteca de templates</h2>
          <p className="td-state">{emptyHint}</p>
        </section>
      </div>
    );
  }

  return (
    <div className="td-home">
      <section className="td-home__greeting" aria-label="Biblioteca de templates">
        <div className="td-template-lib__header">
          <button type="button" className="td-btn td-btn--ghost" onClick={onBack}>
            <ArrowLeft size={16} aria-hidden="true" /> Voltar
          </button>
          <h2 className="td-home__hello">Biblioteca de templates</h2>
        </div>
        <div className="td-home__create-row">
          <button
            type="button"
            className="td-home__create-card"
            disabled={importBusy}
            onClick={() => fileRef.current?.click()}
          >
            <span className="td-home__create-icon" aria-hidden="true">
              <Upload size={28} strokeWidth={2} />
            </span>
            <span className="td-home__create-title">
              {importBusy ? "Validando…" : "Importar MDD"}
            </span>
            <span className="td-home__create-hint">
              Preview e confirmação antes de gravar como rascunho.
            </span>
          </button>
          <input
            ref={fileRef}
            type="file"
            accept=".mdd,application/zip"
            hidden
            onChange={(e) => void onPickImport(e.target.files?.[0] ?? null)}
          />
        </div>
      </section>

      <section className="td-home__library" aria-label="Templates">
        <div className="td-home__library-bar">
          <div className="td-home__filters" role="tablist" aria-label="Filtrar templates">
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
                  "td-home__filter",
                  filter === id ? "td-home__filter--active" : null,
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => setFilter(id)}
              >
                {label}
              </button>
            ))}
          </div>
          <label className="td-home__search">
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
        </div>

        {error ? <div className="td-state">{error}</div> : null}
        {loading ? <div className="td-state">Carregando templates…</div> : null}

        {!loading && items.length === 0 ? (
          <div className="td-state td-template-lib__empty">
            <LayoutTemplate size={32} aria-hidden="true" />
            <p>{emptyHint}</p>
          </div>
        ) : null}

        <ul className="td-template-lib__grid">
          {items.map((item) => (
            <li key={item.id} className="td-template-lib__card">
              <button
                type="button"
                className="td-template-lib__thumb-btn"
                onClick={() => onOpen(item.id)}
              >
                <TemplateThumb template={item} />
              </button>
              <div className="td-template-lib__meta">
                <strong>{item.label}</strong>
                <span className="td-template-lib__badge">
                  {statusLabel(item.status)}
                  {item.isSystem ? " · Sistema" : ""}
                </span>
                {item.description ? <p>{item.description}</p> : null}
              </div>
              <div className="td-template-lib__actions">
                <button type="button" className="td-btn td-btn--ghost" onClick={() => onOpen(item.id)}>
                  Abrir
                </button>
                {item.status !== "published" ? (
                  <button
                    type="button"
                    className="td-btn td-btn--ghost"
                    onClick={() => void runAction(item, "publish")}
                  >
                    Publicar
                  </button>
                ) : (
                  <button
                    type="button"
                    className="td-btn td-btn--ghost"
                    onClick={() => void runAction(item, "unpublish")}
                    disabled={item.isSystem}
                  >
                    Despublicar
                  </button>
                )}
                <button
                  type="button"
                  className="td-btn td-btn--ghost"
                  onClick={() => void runAction(item, "clone")}
                >
                  Duplicar
                </button>
                <button
                  type="button"
                  className="td-btn td-btn--ghost"
                  onClick={() => void runAction(item, "export")}
                >
                  Exportar
                </button>
                <button
                  type="button"
                  className="td-btn td-btn--ghost"
                  onClick={() => void runAction(item, "archive")}
                  disabled={item.isSystem}
                >
                  Arquivar
                </button>
                <button
                  type="button"
                  className="td-btn td-btn--ghost"
                  onClick={() => void runAction(item, "delete")}
                  disabled={item.isSystem}
                >
                  Excluir
                </button>
              </div>
            </li>
          ))}
        </ul>
      </section>

      <HostContainedDialog
        open={Boolean(importPreview)}
        title="Confirmar importação"
        onClose={() => setImportPreview(null)}
      >
        {importPreview ? (
          <div className="td-template-import-preview">
            <p>
              Importar <strong>{importPreview.label}</strong> como rascunho na biblioteca?
            </p>
            {importPreview.description ? <p>{importPreview.description}</p> : null}
            <div className="td-template-import-preview__actions">
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
                className="td-btn"
                onClick={() => void confirmImport()}
                disabled={importBusy}
              >
                {importBusy ? "Importando…" : "Confirmar"}
              </button>
            </div>
          </div>
        ) : null}
      </HostContainedDialog>
    </div>
  );
}
