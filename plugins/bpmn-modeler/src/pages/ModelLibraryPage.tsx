import { useCallback, useEffect, useState } from "react";

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

type Props = {
  getAccessToken?: () => string | undefined;
  capabilities: Capabilities;
  navigate: (path: string) => void;
};

type ArchivedFilter = "active" | "archived" | "all";

function downloadBpmn(filename: string, xml: string) {
  const blob = new Blob([xml], { type: "application/xml" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

/** Model Library (P4 §18) — tabela, busca, filtro de arquivados, paginação. */
export function ModelLibraryPage({ getAccessToken, capabilities, navigate }: Props) {
  const [page, setPage] = useState<ModelListPage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [archived, setArchived] = useState<ArchivedFilter>("active");
  const [sort, setSort] = useState<"updated_at" | "created_at" | "display_name">("updated_at");
  const [direction, setDirection] = useState<"asc" | "desc">("desc");
  const [pageNumber, setPageNumber] = useState(1);
  const [createOpen, setCreateOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [busy, setBusy] = useState(false);

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

  const onDuplicate = async (model: ModelSummary) => {
    const name = window.prompt("Nome da cópia:", `${model.display_name} (cópia)`);
    if (!name?.trim()) return;
    try {
      const outcome = await duplicateModel(model.id, name.trim(), { getAccessToken });
      navigate(`/apps/bpmn-modeler/models/${outcome.model_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Falha ao duplicar.");
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

  const toggleSort = (column: typeof sort) => {
    if (sort === column) {
      setDirection((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSort(column);
      setDirection("desc");
    }
    setPageNumber(1);
  };

  return (
    <div className="bpmnm-page bpmnm-library">
      <header className="bpmnm-page__header">
        <h1>Meu Modelador de Processos</h1>
        <div className="bpmnm-page__actions">
          {capabilities.edit && (
            <>
              <button
                type="button"
                className="bpmnm-btn bpmnm-btn--primary"
                onClick={() => setCreateOpen(true)}
              >
                Novo modelo
              </button>
              <button
                type="button"
                className="bpmnm-btn"
                onClick={() => setImportOpen(true)}
              >
                Importar BPMN
              </button>
            </>
          )}
        </div>
      </header>

      <div className="bpmnm-toolbar" role="search">
        <input
          type="search"
          placeholder="Buscar por nome ou ID…"
          value={query}
          aria-label="Buscar modelos"
          onChange={(e) => {
            setQuery(e.target.value);
            setPageNumber(1);
          }}
        />
        <label className="bpmnm-check">
          <input
            type="checkbox"
            checked={archived !== "active"}
            onChange={(e) => {
              setArchived(e.target.checked ? "all" : "active");
              setPageNumber(1);
            }}
          />
          Incluir arquivados
        </label>
      </div>

      {error ? (
        <div className="bpmnm-error" role="alert">
          {error}{" "}
          <button type="button" className="bpmnm-btn bpmnm-btn--ghost" onClick={() => void load()}>
            Tentar novamente
          </button>
        </div>
      ) : null}

      {loading ? (
        <p className="bpmnm-hint" role="status">Carregando modelos…</p>
      ) : page && page.items.length === 0 ? (
        <div className="bpmnm-empty">
          {query ? (
            <p>Nenhum resultado para a busca.</p>
          ) : (
            <p>Nenhum modelo ainda — crie ou importe um arquivo .bpmn</p>
          )}
        </div>
      ) : (
        <table className="bpmnm-table">
          <thead>
            <tr>
              <th>
                <button type="button" onClick={() => toggleSort("display_name")}>
                  Nome
                </button>
              </th>
              <th>
                <button type="button" onClick={() => toggleSort("updated_at")}>
                  Atualizado em
                </button>
              </th>
              <th>
                <button type="button" onClick={() => toggleSort("created_at")}>
                  Criado em
                </button>
              </th>
              <th>Estado</th>
              <th>Revisões</th>
              <th aria-label="Ações" />
            </tr>
          </thead>
          <tbody>
            {(page?.items ?? []).map((model) => (
              <tr key={model.id}>
                <td>{model.display_name}</td>
                <td>{new Date(model.updated_at).toLocaleString("pt-BR")}</td>
                <td>{new Date(model.created_at).toLocaleString("pt-BR")}</td>
                <td>
                  {model.archived_at ? (
                    <span className="bpmnm-badge">Arquivado</span>
                  ) : (
                    "Ativo"
                  )}
                </td>
                <td>{model.revision_count}</td>
                <td className="bpmnm-row-actions">
                  <button
                    type="button"
                    className="bpmnm-btn bpmnm-btn--ghost"
                    onClick={() => navigate(`/apps/bpmn-modeler/models/${model.id}`)}
                  >
                    Abrir
                  </button>
                  <button
                    type="button"
                    className="bpmnm-btn bpmnm-btn--ghost"
                    onClick={() => void onExport(model)}
                  >
                    Exportar .bpmn
                  </button>
                  {capabilities.manage && (
                    <button
                      type="button"
                      className="bpmnm-btn bpmnm-btn--ghost"
                      onClick={() => void onDuplicate(model)}
                    >
                      Duplicar
                    </button>
                  )}
                  {capabilities.manage && (
                    <button
                      type="button"
                      className="bpmnm-btn bpmnm-btn--ghost"
                      onClick={() => void onArchive(model)}
                    >
                      {model.archived_at ? "Desarquivar" : "Arquivar"}
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {page && (page.page > 1 || page.has_more) ? (
        <nav className="bpmnm-pagination" aria-label="Paginação">
          <button
            type="button"
            className="bpmnm-btn"
            disabled={pageNumber <= 1}
            onClick={() => setPageNumber((p) => p - 1)}
          >
            Anterior
          </button>
          <span>Página {pageNumber}</span>
          <button
            type="button"
            className="bpmnm-btn"
            disabled={!page.has_more}
            onClick={() => setPageNumber((p) => p + 1)}
          >
            Próxima
          </button>
        </nav>
      ) : null}

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
    </div>
  );
}
