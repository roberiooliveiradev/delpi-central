import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Info, MapPinned, Pencil, Plus, Trash2 } from "lucide-react";
import { NativeTextControl } from "@delpi/plugin-ui/index";

import {
  createArea,
  deleteArea,
  fetchAreas,
  setAreaChildren,
  updateArea,
  type AuditArea,
} from "../api/audit5sApi";
import { useAudit5sAdminPermission } from "../hooks/useAudit5sAdminPermission";
import {
  aggregatorAreas,
  childrenOf,
  eligibleSubAreaCandidates,
  leafAreas,
  ungroupedLeafAreas,
} from "../utils/auditAreasHierarchy";

type Props = {
  branch: string;
  pathname?: string;
  onAreasChanged?: () => void;
  onDenied?: () => void;
};

type AggregatorEditorState = {
  kind: "aggregator";
  mode: "create" | "edit";
  parentId: string | null;
  name: string;
  selectedChildIds: string[];
};

type LeafEditorState = {
  kind: "leaf";
  mode: "create" | "edit";
  areaId: string | null;
  name: string;
};

type EditorState = AggregatorEditorState | LeafEditorState;

type PendingDelete = {
  area: AuditArea;
};

const EMPTY_AGGREGATOR_EDITOR: AggregatorEditorState = {
  kind: "aggregator",
  mode: "create",
  parentId: null,
  name: "",
  selectedChildIds: [],
};

export function AuditAreasPage({
  branch,
  pathname,
  onAreasChanged,
  onDenied,
}: Props) {
  const supportsHierarchy = branch === "02";
  const { canAdmin, loading: adminLoading } = useAudit5sAdminPermission(
    branch,
    pathname,
  );
  const onDeniedRef = useRef(onDenied);
  onDeniedRef.current = onDenied;

  const [areas, setAreas] = useState<AuditArea[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editor, setEditor] = useState<EditorState | null>(null);
  const [pendingDelete, setPendingDelete] = useState<PendingDelete | null>(null);

  const loadAreas = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAreas(branch);
      setAreas(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar áreas.");
    } finally {
      setLoading(false);
    }
  }, [branch]);

  useEffect(() => {
    if (adminLoading) return;
    if (!canAdmin) {
      onDeniedRef.current?.();
      return;
    }
    void loadAreas();
  }, [adminLoading, canAdmin, loadAreas]);

  const aggregators = useMemo(() => aggregatorAreas(areas), [areas]);
  const ungrouped = useMemo(() => ungroupedLeafAreas(areas), [areas]);
  const allLeaves = useMemo(() => leafAreas(areas), [areas]);

  const openCreateAggregator = () => {
    setSuccess(null);
    setError(null);
    setEditor({ ...EMPTY_AGGREGATOR_EDITOR, mode: "create" });
  };

  const openEditAggregator = (parent: AuditArea) => {
    setSuccess(null);
    setError(null);
    setEditor({
      kind: "aggregator",
      mode: "edit",
      parentId: parent.id,
      name: parent.name,
      selectedChildIds: childrenOf(areas, parent.id).map((child) => child.id),
    });
  };

  const openCreateLeaf = () => {
    setSuccess(null);
    setError(null);
    setEditor({ kind: "leaf", mode: "create", areaId: null, name: "" });
  };

  const openEditLeaf = (area: AuditArea) => {
    setSuccess(null);
    setError(null);
    setEditor({
      kind: "leaf",
      mode: "edit",
      areaId: area.id,
      name: area.name,
    });
  };

  const closeEditor = () => {
    if (saving) return;
    setEditor(null);
  };

  const toggleChild = (childId: string) => {
    setEditor((prev) => {
      if (!prev || prev.kind !== "aggregator") return prev;
      const selected = new Set(prev.selectedChildIds);
      if (selected.has(childId)) selected.delete(childId);
      else selected.add(childId);
      return { ...prev, selectedChildIds: Array.from(selected) };
    });
  };

  const handleSave = async () => {
    if (!editor) return;
    const name = editor.name.trim();
    if (name.length < 2) {
      setError("Informe um nome com ao menos 2 caracteres.");
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      if (editor.kind === "leaf") {
        if (editor.mode === "create") {
          await createArea(branch, name);
          setSuccess("Área criada.");
        } else if (editor.areaId) {
          await updateArea(editor.areaId, { name });
          setSuccess("Área atualizada.");
        }
      } else {
        let parentId = editor.parentId;
        if (editor.mode === "create") {
          const created = await createArea(branch, name);
          parentId = created.id;
        } else if (parentId) {
          await updateArea(parentId, { name });
        }
        if (!parentId) {
          throw new Error("Área agregadora inválida.");
        }
        await setAreaChildren(parentId, editor.selectedChildIds);
        setSuccess(
          editor.mode === "create"
            ? "Área agregadora criada e subáreas vinculadas."
            : "Área agregadora atualizada.",
        );
      }
      setEditor(null);
      await loadAreas();
      onAreasChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar área.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!pendingDelete) return;
    setDeleting(true);
    setError(null);
    setSuccess(null);
    try {
      await deleteArea(pendingDelete.area.id);
      setSuccess(`Área «${pendingDelete.area.name}» excluída.`);
      setPendingDelete(null);
      await loadAreas();
      onAreasChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir área.");
      setPendingDelete(null);
    } finally {
      setDeleting(false);
    }
  };

  const canDeleteArea = (area: AuditArea) => (area.children_count ?? 0) === 0;

  if (adminLoading || !canAdmin) {
    return <p className="a5s-catalog-loading">Verificando permissão administrativa…</p>;
  }

  if (loading && areas.length === 0) {
    return <p className="a5s-catalog-loading">Carregando áreas…</p>;
  }

  const aggregatorCandidates =
    editor?.kind === "aggregator"
      ? eligibleSubAreaCandidates(areas, editor.parentId)
      : [];

  const renderLeafRow = (area: AuditArea) => (
    <li key={area.id} className="a5s-areas__card a5s-areas__card--leaf">
      <div className="a5s-areas__card-head">
        <div className="a5s-areas__card-title">
          <MapPinned size={16} aria-hidden />
          <strong>{area.name}</strong>
          {area.is_sub_area && area.parent_area_name ? (
            <span className="a5s-areas__badge">{area.parent_area_name}</span>
          ) : null}
        </div>
        <div className="a5s-areas__card-actions">
          <button
            type="button"
            className="a5s-btn a5s-btn--ghost"
            onClick={() => openEditLeaf(area)}
          >
            <Pencil size={14} aria-hidden />
            Editar
          </button>
          <button
            type="button"
            className="a5s-btn a5s-btn--ghost a5s-btn--danger"
            disabled={!canDeleteArea(area)}
            title={
              canDeleteArea(area)
                ? "Excluir área sem auditorias"
                : "Remova as subáreas antes de excluir"
            }
            onClick={() => setPendingDelete({ area })}
          >
            <Trash2 size={14} aria-hidden />
            Excluir
          </button>
        </div>
      </div>
    </li>
  );

  return (
    <div className="a5s-areas">
      <div className="a5s-areas__intro">
        <div>
          <h2 className="a5s-areas__title">
            {supportsHierarchy ? "Áreas — Filial 02" : `Áreas — Filial ${branch}`}
          </h2>
          <p className="a5s-areas__subtitle">
            {supportsHierarchy
              ? "Gerencie áreas folha e agregadoras. Exclusão só é permitida quando a área ainda não tem auditorias e não possui subáreas."
              : "Renomeie ou exclua áreas desta filial. Exclusão só é permitida quando a área ainda não tem auditorias."}
          </p>
        </div>
        <div className="a5s-areas__intro-actions">
          <button type="button" className="a5s-btn a5s-btn--ghost" onClick={openCreateLeaf}>
            <Plus size={16} aria-hidden />
            Nova área
          </button>
          {supportsHierarchy ? (
            <button type="button" className="a5s-btn" onClick={openCreateAggregator}>
              <Plus size={16} aria-hidden />
              Nova agregadora
            </button>
          ) : null}
        </div>
      </div>

      <div className="a5s-catalog__notice" role="note">
        <Info size={18} aria-hidden />
        <p>
          {supportsHierarchy
            ? "Auditorias usam apenas áreas folha (subáreas). A agregadora não aparece no select de nova auditoria."
            : "Áreas usadas em alguma auditoria não podem ser excluídas — renomeie se precisar liberar o nome."}
        </p>
      </div>

      {error ? <div className="a5s-alert a5s-alert--error">{error}</div> : null}
      {success ? <div className="a5s-alert a5s-alert--success">{success}</div> : null}

      {supportsHierarchy ? (
        <section className="a5s-areas__section">
          <h3 className="a5s-areas__section-title">Agregadoras</h3>
          {aggregators.length === 0 ? (
            <p className="a5s-areas__empty">Nenhuma área agregadora cadastrada ainda.</p>
          ) : (
            <ul className="a5s-areas__list">
              {aggregators.map((parent) => {
                const kids = childrenOf(areas, parent.id);
                return (
                  <li key={parent.id} className="a5s-areas__card">
                    <div className="a5s-areas__card-head">
                      <div className="a5s-areas__card-title">
                        <MapPinned size={18} aria-hidden />
                        <strong>{parent.name}</strong>
                        <span className="a5s-areas__badge">
                          {kids.length} subárea{kids.length === 1 ? "" : "s"}
                        </span>
                      </div>
                      <div className="a5s-areas__card-actions">
                        <button
                          type="button"
                          className="a5s-btn a5s-btn--ghost"
                          onClick={() => openEditAggregator(parent)}
                        >
                          <Pencil size={14} aria-hidden />
                          Editar
                        </button>
                        <button
                          type="button"
                          className="a5s-btn a5s-btn--ghost a5s-btn--danger"
                          disabled={!canDeleteArea(parent)}
                          title={
                            canDeleteArea(parent)
                              ? "Excluir agregadora sem subáreas"
                              : "Remova as subáreas antes de excluir"
                          }
                          onClick={() => setPendingDelete({ area: parent })}
                        >
                          <Trash2 size={14} aria-hidden />
                          Excluir
                        </button>
                      </div>
                    </div>
                    {kids.length > 0 ? (
                      <ul className="a5s-areas__children">
                        {kids.map((child) => (
                          <li key={child.id} className="a5s-areas__child-row">
                            <span>{child.name}</span>
                            <div className="a5s-areas__card-actions">
                              <button
                                type="button"
                                className="a5s-btn a5s-btn--ghost"
                                onClick={() => openEditLeaf(child)}
                              >
                                <Pencil size={14} aria-hidden />
                                Editar
                              </button>
                              <button
                                type="button"
                                className="a5s-btn a5s-btn--ghost a5s-btn--danger"
                                onClick={() => setPendingDelete({ area: child })}
                              >
                                <Trash2 size={14} aria-hidden />
                                Excluir
                              </button>
                            </div>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="a5s-areas__empty">Sem subáreas vinculadas.</p>
                    )}
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      ) : null}

      <section className="a5s-areas__section">
        <h3 className="a5s-areas__section-title">
          {supportsHierarchy ? "Áreas sem agrupamento" : "Áreas cadastradas"}
        </h3>
        {(supportsHierarchy ? ungrouped : allLeaves).length === 0 ? (
          <p className="a5s-areas__empty">
            {supportsHierarchy
              ? "Todas as áreas folha estão vinculadas."
              : "Nenhuma área cadastrada ainda."}
          </p>
        ) : (
          <ul className="a5s-areas__list">
            {(supportsHierarchy ? ungrouped : allLeaves).map(renderLeafRow)}
          </ul>
        )}
      </section>

      {editor ? (
        <div
          className="a5s-confirm-overlay"
          role="presentation"
          onClick={closeEditor}
        >
          <div
            className="a5s-confirm-dialog a5s-areas-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="a5s-areas-modal-title"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id="a5s-areas-modal-title" className="a5s-catalog-modal__title">
              {editor.kind === "leaf"
                ? editor.mode === "create"
                  ? "Nova área"
                  : "Editar área"
                : editor.mode === "create"
                  ? "Nova área agregadora"
                  : "Editar área agregadora"}
            </h2>
            <label className="a5s-areas-modal__field" htmlFor="a5s-area-name">
              Nome
              <NativeTextControl
                id="a5s-area-name"
                type="text"
                value={editor.name}
                onChange={(value) =>
                  setEditor((prev) => (prev ? { ...prev, name: value } : prev))
                }
                placeholder={
                  editor.kind === "aggregator" ? "Ex.: Montagem ES" : "Ex.: Usinagem"
                }
              />
            </label>
            {editor.kind === "aggregator" ? (
              <fieldset className="a5s-areas-modal__fieldset">
                <legend>Subáreas</legend>
                <p className="a5s-areas-modal__hint">
                  Selecione as áreas já cadastradas que fazem parte desta agregadora.
                </p>
                <div className="a5s-areas-modal__checks">
                  {aggregatorCandidates.length === 0 ? (
                    <p className="a5s-areas__empty">Nenhuma área elegível disponível.</p>
                  ) : (
                    aggregatorCandidates.map((area) => {
                      const checked = editor.selectedChildIds.includes(area.id);
                      return (
                        <label key={area.id} className="a5s-areas-modal__check">
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleChild(area.id)}
                          />
                          <span>
                            {area.name}
                            {area.is_sub_area && area.parent_area_id !== editor.parentId
                              ? " (já vinculada a outra agregadora)"
                              : ""}
                          </span>
                        </label>
                      );
                    })
                  )}
                </div>
              </fieldset>
            ) : null}
            <div className="a5s-catalog-modal__actions">
              <button
                type="button"
                className="a5s-btn a5s-btn--ghost"
                onClick={closeEditor}
                disabled={saving}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="a5s-btn"
                onClick={() => void handleSave()}
                disabled={saving}
              >
                {saving ? "Salvando…" : "Salvar"}
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {pendingDelete ? (
        <div
          className="a5s-confirm-overlay"
          role="presentation"
          onClick={() => !deleting && setPendingDelete(null)}
        >
          <div
            className="a5s-confirm-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="a5s-delete-area-title"
            aria-describedby="a5s-delete-area-desc"
            onClick={(event) => event.stopPropagation()}
          >
            <h2 id="a5s-delete-area-title" className="a5s-confirm-dialog__title">
              Excluir área?
            </h2>
            <p id="a5s-delete-area-desc" className="a5s-confirm-dialog__text">
              A área «{pendingDelete.area.name}» será removida permanentemente. Só é
              permitido se ela ainda não tiver auditorias
              {supportsHierarchy ? " e não tiver subáreas vinculadas" : ""}.
            </p>
            <div className="a5s-confirm-dialog__actions">
              <button
                type="button"
                className="a5s-btn a5s-btn--ghost"
                disabled={deleting}
                onClick={() => setPendingDelete(null)}
              >
                Cancelar
              </button>
              <button
                type="button"
                className="a5s-btn a5s-btn--danger"
                disabled={deleting}
                onClick={() => void handleDelete()}
              >
                {deleting ? "Excluindo…" : "Excluir"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
