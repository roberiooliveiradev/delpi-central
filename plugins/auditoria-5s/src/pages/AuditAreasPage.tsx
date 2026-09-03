import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Info, MapPinned, Pencil, Plus } from "lucide-react";
import { NativeTextControl } from "@delpi/plugin-ui/index";

import {
  createArea,
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
  ungroupedLeafAreas,
} from "../utils/auditAreasHierarchy";

type Props = {
  branch: string;
  pathname?: string;
  onAreasChanged?: () => void;
  onDenied?: () => void;
};

type EditorState = {
  mode: "create" | "edit";
  parentId: string | null;
  name: string;
  selectedChildIds: string[];
};

const EMPTY_EDITOR: EditorState = {
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
  const { canAdmin, loading: adminLoading } = useAudit5sAdminPermission(
    branch,
    pathname,
  );
  const onDeniedRef = useRef(onDenied);
  onDeniedRef.current = onDenied;

  const [areas, setAreas] = useState<AuditArea[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [editor, setEditor] = useState<EditorState | null>(null);

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
    if (!canAdmin || branch !== "02") {
      onDeniedRef.current?.();
      return;
    }
    void loadAreas();
  }, [adminLoading, canAdmin, branch, loadAreas]);

  const aggregators = useMemo(() => aggregatorAreas(areas), [areas]);
  const ungrouped = useMemo(() => ungroupedLeafAreas(areas), [areas]);

  const openCreate = () => {
    setSuccess(null);
    setError(null);
    setEditor({ ...EMPTY_EDITOR, mode: "create" });
  };

  const openEdit = (parent: AuditArea) => {
    setSuccess(null);
    setError(null);
    setEditor({
      mode: "edit",
      parentId: parent.id,
      name: parent.name,
      selectedChildIds: childrenOf(areas, parent.id).map((child) => child.id),
    });
  };

  const closeEditor = () => {
    if (saving) return;
    setEditor(null);
  };

  const toggleChild = (childId: string) => {
    setEditor((prev) => {
      if (!prev) return prev;
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
      setError("Informe um nome com ao menos 2 caracteres para a área agregadora.");
      return;
    }

    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
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
      setEditor(null);
      await loadAreas();
      onAreasChanged?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar área agregadora.");
    } finally {
      setSaving(false);
    }
  };

  if (adminLoading || !canAdmin) {
    return <p className="a5s-catalog-loading">Verificando permissão administrativa…</p>;
  }

  if (branch !== "02") {
    return (
      <p className="a5s-catalog-loading">
        Hierarquia de áreas está disponível apenas na filial 02.
      </p>
    );
  }

  if (loading && areas.length === 0) {
    return <p className="a5s-catalog-loading">Carregando áreas…</p>;
  }

  const candidates = editor
    ? eligibleSubAreaCandidates(areas, editor.parentId)
    : [];

  return (
    <div className="a5s-areas">
      <div className="a5s-areas__intro">
        <div>
          <h2 className="a5s-areas__title">Áreas agregadoras — Filial 02</h2>
          <p className="a5s-areas__subtitle">
            Cadastre uma área maior e vincule as áreas já existentes como subáreas. A
            média da agregadora no dashboard é a média das médias das subáreas.
          </p>
        </div>
        <button type="button" className="a5s-btn" onClick={openCreate}>
          <Plus size={16} aria-hidden />
          Nova agregadora
        </button>
      </div>

      <div className="a5s-catalog__notice" role="note">
        <Info size={18} aria-hidden />
        <p>
          Auditorias continuam sendo feitas apenas nas subáreas (folhas). A área
          agregadora não aparece no select de nova auditoria.
        </p>
      </div>

      {error ? <div className="a5s-alert a5s-alert--error">{error}</div> : null}
      {success ? <div className="a5s-alert a5s-alert--success">{success}</div> : null}

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
                    <button
                      type="button"
                      className="a5s-btn a5s-btn--ghost"
                      onClick={() => openEdit(parent)}
                    >
                      <Pencil size={14} aria-hidden />
                      Editar
                    </button>
                  </div>
                  {kids.length > 0 ? (
                    <ul className="a5s-areas__children">
                      {kids.map((child) => (
                        <li key={child.id}>{child.name}</li>
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

      <section className="a5s-areas__section">
        <h3 className="a5s-areas__section-title">Áreas sem agrupamento</h3>
        {ungrouped.length === 0 ? (
          <p className="a5s-areas__empty">Todas as áreas folha estão vinculadas.</p>
        ) : (
          <ul className="a5s-areas__chips">
            {ungrouped.map((area) => (
              <li key={area.id}>{area.name}</li>
            ))}
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
              {editor.mode === "create" ? "Nova área agregadora" : "Editar área agregadora"}
            </h2>
            <label className="a5s-areas-modal__field" htmlFor="a5s-aggregator-name">
              Nome
              <NativeTextControl
                id="a5s-aggregator-name"
                type="text"
                value={editor.name}
                onChange={(value) =>
                  setEditor((prev) => (prev ? { ...prev, name: value } : prev))
                }
                placeholder="Ex.: Montagem ES"
              />
            </label>
            <fieldset className="a5s-areas-modal__fieldset">
              <legend>Subáreas</legend>
              <p className="a5s-areas-modal__hint">
                Selecione as áreas já cadastradas que fazem parte desta agregadora.
              </p>
              <div className="a5s-areas-modal__checks">
                {candidates.length === 0 ? (
                  <p className="a5s-areas__empty">Nenhuma área elegível disponível.</p>
                ) : (
                  candidates.map((area) => {
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
    </div>
  );
}
