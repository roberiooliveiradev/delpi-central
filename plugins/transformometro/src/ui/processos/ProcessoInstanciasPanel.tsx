import { useEffect, useMemo, useState } from "react";
import { Copy, Pencil, Plus, Trash2 } from "lucide-react";

import type { DataTableColumn } from "../../components/DataTable";
import { DataTableSection } from "../../components/DataTableSection";
import type { OptionsData, ProcessoInstancia } from "../../data/api/transformometroApi";
import { filterSetoresByFilial, resolveSetorIdForFilial } from "../../utils/setores";

type Props = {
  instancias: ProcessoInstancia[];
  selectedInstanciaId: string | null;
  options: OptionsData;
  busy?: boolean;
  initialShowForm?: boolean;
  onSelect: (instanciaId: string) => void;
  onCreate: (payload: {
    filial_id?: string;
    todas_filiais_ativas?: boolean;
    setor_ids: string[];
    rotulo_instancia?: string;
  }) => Promise<void>;
  onUpdate: (
    instanciaId: string,
    payload: {
      setor_ids: string[];
      rotulo_instancia?: string;
      status_instancia?: string;
    }
  ) => Promise<void>;
  onDelete: (instanciaId: string) => Promise<void>;
  onDuplicate: (payload: {
    origemInstanciaId: string;
    filial_id: string;
    setor_id: string;
    rotulo_instancia?: string;
  }) => Promise<void>;
};

function instanciaFilialKey(row: ProcessoInstancia): string {
  if (row.todas_filiais_ativas) return "__todas__";
  return String(row.codigo_filial ?? row.filial_id ?? "").trim().toLowerCase();
}

function instanciaSetorKeys(row: ProcessoInstancia): string[] {
  if (row.setores?.length) {
    return row.setores
      .map((setor) => String(setor.codigo_setor ?? setor.setor_id ?? "").trim().toLowerCase())
      .filter(Boolean);
  }
  const single = String(row.codigo_setor ?? row.setor_id ?? "").trim().toLowerCase();
  return single ? [single] : [];
}

function instanciaSetorIdsForForm(row: ProcessoInstancia, setores: OptionsData["setores"]): string[] {
  const keys = instanciaSetorKeys(row);
  return keys.map((key) => {
    const match = setores.find((setor) => setor.id.toLowerCase() === key);
    return match?.id ?? key;
  });
}

function formatSetores(row: ProcessoInstancia): string {
  if (row.setores?.length) {
    return row.setores
      .map((setor) => `${setor.codigo_setor ?? setor.setor_id} — ${setor.nome_setor ?? ""}`.trim())
      .join("; ");
  }
  return `${row.codigo_setor ?? row.setor_id ?? ""} — ${row.nome_setor ?? ""}`.trim();
}

function defaultSetorIds(
  setores: OptionsData["setores"],
  filialId: string,
  instancias: ProcessoInstancia[],
  excludeInstanciaId?: string | null
): string[] {
  const used = new Set<string>();
  for (const row of instancias) {
    if (excludeInstanciaId && row.instancia_id === excludeInstanciaId) continue;
    if (instanciaFilialKey(row) !== filialId.trim().toLowerCase()) continue;
    for (const key of instanciaSetorKeys(row)) used.add(key);
  }
  const first = filterSetoresByFilial(setores, filialId).find(
    (setor) => !used.has(setor.id.toLowerCase())
  );
  return first ? [first.id] : [];
}

export function ProcessoInstanciasPanel({
  instancias,
  selectedInstanciaId,
  options,
  busy = false,
  initialShowForm = false,
  onSelect,
  onCreate,
  onUpdate,
  onDelete,
  onDuplicate,
}: Props) {
  const [showForm, setShowForm] = useState(initialShowForm);
  const [editingInstanciaId, setEditingInstanciaId] = useState<string | null>(null);
  const [duplicateSourceId, setDuplicateSourceId] = useState<string | null>(null);
  const [todasFiliais, setTodasFiliais] = useState(false);
  const [filialId, setFilialId] = useState(options.filiais[0]?.id ?? "01");
  const [setorIds, setSetorIds] = useState<string[]>(() =>
    defaultSetorIds(options.setores, options.filiais[0]?.id ?? "01", instancias)
  );
  const [setorId, setSetorId] = useState(
    resolveSetorIdForFilial(options.setores, options.filiais[0]?.id ?? "01", "")
  );
  const [rotulo, setRotulo] = useState("");
  const [statusInstancia, setStatusInstancia] = useState("ativo");
  const [saving, setSaving] = useState(false);

  const editingInstancia = useMemo(
    () => instancias.find((row) => row.instancia_id === editingInstanciaId) ?? null,
    [editingInstanciaId, instancias]
  );

  useEffect(() => {
    if (initialShowForm) {
      setShowForm(true);
    }
  }, [initialShowForm]);

  const scopeFilialKey = useMemo(() => {
    if (editingInstancia) return instanciaFilialKey(editingInstancia);
    return todasFiliais ? "__todas__" : filialId.trim().toLowerCase();
  }, [editingInstancia, filialId, todasFiliais]);

  const setoresDisponiveis = useMemo(() => {
    if (editingInstancia?.todas_filiais_ativas || todasFiliais) return options.setores;
    const codigo = editingInstancia?.codigo_filial ?? filialId;
    return filterSetoresByFilial(options.setores, codigo);
  }, [editingInstancia, filialId, options.setores, todasFiliais]);

  const usedSetorIdsForScope = useMemo(() => {
    const used = new Set<string>();
    for (const row of instancias) {
      if (editingInstanciaId && row.instancia_id === editingInstanciaId) continue;
      if (instanciaFilialKey(row) !== scopeFilialKey) continue;
      for (const key of instanciaSetorKeys(row)) used.add(key);
    }
    return used;
  }, [editingInstanciaId, instancias, scopeFilialKey]);

  const pendingSetorIds = useMemo(
    () => setorIds.filter((id) => !usedSetorIdsForScope.has(id.trim().toLowerCase())),
    [setorIds, usedSetorIdsForScope]
  );

  function resetForm() {
    setShowForm(false);
    setEditingInstanciaId(null);
    setDuplicateSourceId(null);
    setTodasFiliais(false);
    setRotulo("");
    setStatusInstancia("ativo");
  }

  function openCreateForm() {
    resetForm();
    setFilialId(options.filiais[0]?.id ?? "01");
    setSetorIds(defaultSetorIds(options.setores, options.filiais[0]?.id ?? "01", instancias));
    setShowForm(true);
  }

  function startEdit(row: ProcessoInstancia) {
    setDuplicateSourceId(null);
    setEditingInstanciaId(row.instancia_id);
    setTodasFiliais(Boolean(row.todas_filiais_ativas));
    setFilialId(row.codigo_filial ?? row.filial_id ?? "01");
    setSetorIds(instanciaSetorIdsForForm(row, options.setores));
    setRotulo(row.rotulo_instancia ?? "");
    setStatusInstancia(row.status_instancia ?? "ativo");
    setShowForm(true);
  }

  function toggleSetor(setorIdValue: string) {
    const key = setorIdValue.trim().toLowerCase();
    if (!editingInstanciaId && usedSetorIdsForScope.has(key)) return;
    if (editingInstanciaId) {
      const isChecked = setorIds.some((id) => id.toLowerCase() === key);
      if (isChecked && setorIds.length <= 1) return;
      if (!isChecked && usedSetorIdsForScope.has(key)) return;
    }
    setSetorIds((current) =>
      current.some((id) => id.toLowerCase() === key)
        ? current.filter((id) => id.toLowerCase() !== key)
        : [...current, setorIdValue]
    );
  }

  async function handleDelete(row: ProcessoInstancia) {
    if (
      !window.confirm(
        `Excluir instância ${row.todas_filiais_ativas ? "todas filiais" : row.codigo_filial ?? row.filial_id}? Só é possível sem revisões cadastradas.`
      )
    ) {
      return;
    }
    setSaving(true);
    try {
      await onDelete(row.instancia_id);
      if (editingInstanciaId === row.instancia_id) resetForm();
    } finally {
      setSaving(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      if (editingInstanciaId) {
        await onUpdate(editingInstanciaId, {
          setor_ids: setorIds,
          rotulo_instancia: rotulo.trim() || undefined,
          status_instancia: statusInstancia,
        });
      } else if (duplicateSourceId) {
        await onDuplicate({
          origemInstanciaId: duplicateSourceId,
          filial_id: filialId,
          setor_id: setorId,
          rotulo_instancia: rotulo.trim() || undefined,
        });
      } else {
        await onCreate({
          filial_id: todasFiliais ? undefined : filialId,
          todas_filiais_ativas: todasFiliais,
          setor_ids: pendingSetorIds,
          rotulo_instancia: rotulo.trim() || undefined,
        });
      }
      resetForm();
    } finally {
      setSaving(false);
    }
  }

  const columns = useMemo<DataTableColumn<ProcessoInstancia>[]>(
    () => [
      {
        key: "filial",
        header: "Filial",
        render: (row) =>
          row.todas_filiais_ativas
            ? "Todas as filiais ativas"
            : `${row.codigo_filial ?? row.filial_id} — ${row.nome_filial ?? ""}`.trim(),
      },
      {
        key: "status",
        header: "Status",
        render: (row) => row.status_instancia ?? "ativo",
      },
      {
        key: "setor",
        header: "Setores",
        render: (row) => formatSetores(row) || "—",
      },
      {
        key: "rotulo",
        header: "Rótulo",
        render: (row) => row.rotulo_instancia ?? "—",
      },
      {
        key: "acoes",
        header: "",
        render: (row) => (
          <div className="ds-table__actions">
            <button
              type="button"
              className={`ds-ghost-btn${selectedInstanciaId === row.instancia_id ? " ds-ghost-btn--active" : ""}`}
              onClick={() => onSelect(row.instancia_id)}
            >
              {selectedInstanciaId === row.instancia_id ? "Selecionada" : "Selecionar"}
            </button>
            <button type="button" className="ds-ghost-btn" onClick={() => startEdit(row)}>
              <Pencil size={14} />
              Editar
            </button>
            <button
              type="button"
              className="ds-ghost-btn"
              onClick={() => {
                setEditingInstanciaId(null);
                setDuplicateSourceId(row.instancia_id);
                setTodasFiliais(false);
                setFilialId(row.codigo_filial ?? row.filial_id ?? "01");
                setSetorId(row.codigo_setor ?? row.setor_id ?? "");
                setRotulo("");
                setShowForm(true);
              }}
            >
              <Copy size={14} />
              Replicar
            </button>
            <button
              type="button"
              className="ds-ghost-btn"
              disabled={busy || saving}
              onClick={() => void handleDelete(row)}
            >
              <Trash2 size={14} />
              Excluir
            </button>
          </div>
        ),
      },
    ],
    [busy, onSelect, saving, selectedInstanciaId]
  );

  const formTitle = editingInstanciaId
    ? "Editar instância operacional"
    : duplicateSourceId
      ? "Replicar instância"
      : "Nova instância operacional";

  const submitLabel = saving
    ? "Salvando…"
    : editingInstanciaId
      ? "Salvar alterações"
      : duplicateSourceId
        ? "Replicar timeline"
        : "Criar instância";

  const canSubmit = editingInstanciaId
    ? setorIds.length > 0
    : duplicateSourceId
      ? Boolean(filialId && setorId)
      : pendingSetorIds.length > 0 && (todasFiliais || Boolean(filialId));

  return (
    <>
      <section className="ds-card">
        <div className="ds-table-section__header">
          <div>
            <h2 className="ds-section-title">Instâncias operacionais</h2>
            <p className="ds-hint">
              Cada instância pertence a uma filial (ou a todas as ativas) e amarra um ou mais
              setores. As revisões ficam na instância.
            </p>
          </div>
          <button type="button" className="ds-primary-btn" disabled={busy} onClick={openCreateForm}>
            <Plus size={16} />
            Nova instância
          </button>
        </div>
        <DataTableSection
          title=""
          columns={columns}
          rows={instancias}
          rowKey={(row) => row.instancia_id}
          hideSearch
          emptyMessage="Nenhuma instância cadastrada."
        />
      </section>

      {showForm ? (
        <section className="ds-card ds-cadastro-form">
          <h2 className="ds-section-title">{formTitle}</h2>
          {!duplicateSourceId && !editingInstanciaId ? (
            <p className="ds-hint">
              Selecione a filial e marque os setores vinculados. Setores já amarrados nesta filial
              aparecem desabilitados.
            </p>
          ) : null}
          {editingInstanciaId ? (
            <p className="ds-hint">
              A filial não pode ser alterada quando já existem revisões. Ajuste setores, rótulo e
              status.
            </p>
          ) : null}
          <form onSubmit={handleSubmit}>
            <div className="ds-filters-row">
              {!duplicateSourceId && !editingInstanciaId ? (
                <div className="ds-filter-box ds-filter-box--wide">
                  <label className="tm-inst-setores-label">
                    <input
                      type="checkbox"
                      checked={todasFiliais}
                      onChange={(e) => {
                        const next = e.target.checked;
                        setTodasFiliais(next);
                        if (!next) {
                          setSetorIds(defaultSetorIds(options.setores, filialId, instancias));
                        }
                      }}
                    />{" "}
                    Todas as filiais ativas
                  </label>
                </div>
              ) : null}

              {!todasFiliais || duplicateSourceId || editingInstanciaId ? (
                <div className="ds-filter-box">
                  <label htmlFor="tm-inst-filial">Filial *</label>
                  <select
                    id="tm-inst-filial"
                    value={filialId}
                    disabled={duplicateSourceId !== null || editingInstanciaId !== null}
                    onChange={(e) => {
                      const next = e.target.value;
                      setFilialId(next);
                      if (duplicateSourceId) {
                        setSetorId(resolveSetorIdForFilial(options.setores, next, setorId));
                      } else {
                        setSetorIds(defaultSetorIds(options.setores, next, instancias));
                      }
                    }}
                  >
                    {options.filiais.map((filial) => (
                      <option key={filial.id} value={filial.id}>
                        {filial.id} — {filial.label}
                      </option>
                    ))}
                  </select>
                </div>
              ) : null}

              {editingInstanciaId ? (
                <div className="ds-filter-box">
                  <label htmlFor="tm-inst-status">Status *</label>
                  <select
                    id="tm-inst-status"
                    value={statusInstancia}
                    onChange={(e) => setStatusInstancia(e.target.value)}
                  >
                    <option value="ativo">ativo</option>
                    <option value="inativo">inativo</option>
                  </select>
                </div>
              ) : null}

              {duplicateSourceId ? (
                <div className="ds-filter-box">
                  <label htmlFor="tm-inst-setor">Setor destino *</label>
                  <select
                    id="tm-inst-setor"
                    value={setorId}
                    onChange={(e) => setSetorId(e.target.value)}
                    disabled={setoresDisponiveis.length === 0}
                  >
                    {setoresDisponiveis.map((setor) => (
                      <option key={setor.id} value={setor.id}>
                        {setor.label}
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="ds-filter-box ds-filter-box--wide">
                  <span className="tm-inst-setores-label">Setores *</span>
                  <div className="tm-inst-setores-grid" role="group" aria-label="Setores da instância">
                    {setoresDisponiveis.length === 0 ? (
                      <p className="ds-hint">Nenhum setor disponível para esta filial.</p>
                    ) : (
                      setoresDisponiveis.map((setor) => {
                        const usedByOther = usedSetorIdsForScope.has(setor.id.toLowerCase());
                        const checked = setorIds.some(
                          (id) => id.toLowerCase() === setor.id.toLowerCase()
                        );
                        const disabled =
                          usedByOther ||
                          (!!editingInstanciaId && checked && setorIds.length <= 1);
                        return (
                          <label
                            key={setor.id}
                            className={`tm-inst-setor-option${usedByOther ? " tm-inst-setor-option--used" : ""}`}
                          >
                            <input
                              type="checkbox"
                              checked={checked}
                              disabled={disabled}
                              onChange={() => toggleSetor(setor.id)}
                            />
                            <span>
                              {setor.label}
                              {usedByOther ? " (outra instância)" : ""}
                            </span>
                          </label>
                        );
                      })
                    )}
                  </div>
                </div>
              )}

              <div className="ds-filter-box ds-filter-box--wide">
                <label htmlFor="tm-inst-rotulo">Rótulo (opcional)</label>
                <input
                  id="tm-inst-rotulo"
                  value={rotulo}
                  onChange={(e) => setRotulo(e.target.value)}
                  placeholder="Ex.: Matriz — rollout Q2"
                />
              </div>
            </div>
            <div className="ds-cadastro-form__actions">
              <button type="submit" className="ds-primary-btn" disabled={saving || !canSubmit}>
                {submitLabel}
              </button>
              <button type="button" className="ds-ghost-btn" disabled={saving} onClick={resetForm}>
                Cancelar
              </button>
            </div>
          </form>
        </section>
      ) : null}
    </>
  );
}
