import { useEffect, useMemo, useState } from "react";
import { Copy, Pencil, Plus, Trash2 } from "lucide-react";

import type { DataTableColumn } from "../../components/DataTable";
import { DataTableSection } from "../../components/DataTableSection";
import type { OptionsData, ProcessoInstancia } from "../../data/api/transformometroApi";
import { filterSetoresByFilial, resolveSetorIdForFilial } from "../../utils/setores";

type CreatePayload = {
  filial_id?: string;
  todas_filiais_ativas?: boolean;
  setor_ids: string[];
  rotulo_instancia?: string;
};

type Props = {
  instancias: ProcessoInstancia[];
  selectedInstanciaId: string | null;
  options: OptionsData;
  busy?: boolean;
  initialShowForm?: boolean;
  /** IDs de instâncias que já possuem revisões (bloqueiam a troca de filial). */
  instanciasComRevisao?: string[];
  onSelect: (instanciaId: string) => void;
  onCreate: (payload: CreatePayload) => Promise<void>;
  onUpdate: (
    instanciaId: string,
    payload: {
      setor_ids: string[];
      rotulo_instancia?: string;
      status_instancia?: string;
      filial_id?: string;
      todas_filiais_ativas?: boolean;
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
  instancias: ProcessoInstancia[]
): string[] {
  const used = new Set<string>();
  for (const row of instancias) {
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
  instanciasComRevisao = [],
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
  const [filialIds, setFilialIds] = useState<string[]>(() =>
    options.filiais[0]?.id ? [options.filiais[0].id] : []
  );
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

  const isCreate = !editingInstanciaId && !duplicateSourceId;

  const editingHasRevisoes = editingInstanciaId
    ? instanciasComRevisao.some((id) => id === editingInstanciaId)
    : false;

  useEffect(() => {
    if (initialShowForm) {
      setShowForm(true);
    }
  }, [initialShowForm]);

  // Setores já utilizados por outras instâncias, agrupados por filial (chave normalizada).
  const usedSetorKeysByFilial = useMemo(() => {
    const map = new Map<string, Set<string>>();
    for (const row of instancias) {
      if (editingInstanciaId && row.instancia_id === editingInstanciaId) continue;
      const filialKey = instanciaFilialKey(row);
      let set = map.get(filialKey);
      if (!set) {
        set = new Set<string>();
        map.set(filialKey, set);
      }
      for (const key of instanciaSetorKeys(row)) set.add(key);
    }
    return map;
  }, [editingInstanciaId, instancias]);

  // Setores disponíveis conforme o modo (criar/editar multi-filial ou replicar).
  const setoresDisponiveis = useMemo(() => {
    if (duplicateSourceId) {
      return filterSetoresByFilial(options.setores, filialId);
    }
    if (todasFiliais) return options.setores;
    if (filialIds.length === 0) return [];
    const seen = new Set<string>();
    const out: OptionsData["setores"] = [];
    for (const fid of filialIds) {
      for (const setor of filterSetoresByFilial(options.setores, fid)) {
        const key = setor.id.toLowerCase();
        if (!seen.has(key)) {
          seen.add(key);
          out.push(setor);
        }
      }
    }
    return out;
  }, [duplicateSourceId, filialId, todasFiliais, filialIds, options.setores]);

  // Payloads por filial selecionada (novo ou editar); filtra setores válidos/livres por filial.
  const filialPayloads = useMemo<CreatePayload[]>(() => {
    if (duplicateSourceId || todasFiliais) return [];
    const rotuloValue = rotulo.trim() || undefined;
    const payloads: CreatePayload[] = [];
    for (const fid of filialIds) {
      const filialKey = fid.trim().toLowerCase();
      const available = new Set(
        filterSetoresByFilial(options.setores, fid).map((setor) => setor.id.toLowerCase())
      );
      const used = usedSetorKeysByFilial.get(filialKey) ?? new Set<string>();
      const valid = setorIds.filter(
        (id) => available.has(id.toLowerCase()) && !used.has(id.toLowerCase())
      );
      if (valid.length > 0) {
        payloads.push({
          filial_id: fid,
          todas_filiais_ativas: false,
          setor_ids: valid,
          rotulo_instancia: rotuloValue,
        });
      }
    }
    return payloads;
  }, [
    duplicateSourceId,
    rotulo,
    todasFiliais,
    setorIds,
    filialIds,
    options.setores,
    usedSetorKeysByFilial,
  ]);

  // Quantas instâncias o submit produz no modo criar (todas = 1 consolidada).
  const createCount = todasFiliais ? (setorIds.length > 0 ? 1 : 0) : filialPayloads.length;

  // Filiais selecionadas que ficariam sem nenhum setor válido (aviso ao usuário).
  const skippedFiliais = useMemo(() => {
    if (duplicateSourceId || todasFiliais) return [] as string[];
    const withPayload = new Set(filialPayloads.map((p) => (p.filial_id ?? "").toLowerCase()));
    return filialIds.filter((fid) => !withPayload.has(fid.toLowerCase()));
  }, [duplicateSourceId, todasFiliais, filialPayloads, filialIds]);

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
    const firstFilial = options.filiais[0]?.id ?? "01";
    setFilialId(firstFilial);
    setFilialIds(firstFilial ? [firstFilial] : []);
    setSetorIds(defaultSetorIds(options.setores, firstFilial, instancias));
    setShowForm(true);
  }

  function startEdit(row: ProcessoInstancia) {
    setDuplicateSourceId(null);
    setEditingInstanciaId(row.instancia_id);
    setTodasFiliais(Boolean(row.todas_filiais_ativas));
    const filialAtual = row.codigo_filial ?? row.filial_id ?? "01";
    setFilialId(filialAtual);
    setFilialIds(row.todas_filiais_ativas ? [] : [filialAtual]);
    setSetorIds(instanciaSetorIdsForForm(row, options.setores));
    setRotulo(row.rotulo_instancia ?? "");
    setStatusInstancia(row.status_instancia ?? "ativo");
    setShowForm(true);
  }

  function startDuplicate(row: ProcessoInstancia) {
    setEditingInstanciaId(null);
    setDuplicateSourceId(row.instancia_id);
    setTodasFiliais(false);
    setFilialId(row.codigo_filial ?? row.filial_id ?? "01");
    setSetorId(row.codigo_setor ?? row.setor_id ?? "");
    setRotulo("");
    setShowForm(true);
  }

  function toggleFilial(value: string) {
    const key = value.trim().toLowerCase();
    setFilialIds((current) => {
      const next = current.some((id) => id.toLowerCase() === key)
        ? current.filter((id) => id.toLowerCase() !== key)
        : [...current, value];
      // Garante ao menos um setor pré-selecionado quando a primeira filial é marcada.
      if (next.length > 0 && setorIds.length === 0) {
        setSetorIds(defaultSetorIds(options.setores, next[0], instancias));
      }
      return next;
    });
  }

  function toggleSetor(setorIdValue: string) {
    setSetorIds((current) =>
      current.some((id) => id.toLowerCase() === setorIdValue.toLowerCase())
        ? current.filter((id) => id.toLowerCase() !== setorIdValue.toLowerCase())
        : [...current, setorIdValue]
    );
  }

  // Estado de cada setor na grade: se está marcado e se deve ficar desabilitado.
  function setorState(setorIdValue: string): { checked: boolean; disabled: boolean; used: boolean } {
    const key = setorIdValue.toLowerCase();
    const checked = setorIds.some((id) => id.toLowerCase() === key);
    if (todasFiliais) {
      return { checked, disabled: false, used: false };
    }
    if (filialIds.length <= 1) {
      const filialKey = (filialIds[0] ?? "").toLowerCase();
      const usedByOther = (usedSetorKeysByFilial.get(filialKey) ?? new Set()).has(key);
      return { checked, disabled: usedByOther, used: usedByOther };
    }
    // Multi-filial: só desabilita quando o setor já está em uso em TODAS as filiais que o oferecem.
    let offering = 0;
    let usedEverywhere = true;
    for (const fid of filialIds) {
      const available = filterSetoresByFilial(options.setores, fid).some(
        (setor) => setor.id.toLowerCase() === key
      );
      if (!available) continue;
      offering += 1;
      if (!(usedSetorKeysByFilial.get(fid.toLowerCase()) ?? new Set()).has(key)) {
        usedEverywhere = false;
      }
    }
    const fullyUsed = offering > 0 && usedEverywhere;
    return { checked, disabled: fullyUsed, used: fullyUsed };
  }

  async function handleDelete(row: ProcessoInstancia) {
    if (
      !window.confirm(
        `Excluir instância ${row.todas_filiais_ativas ? "todas as unidades" : row.codigo_filial ?? row.filial_id}? Só é possível sem revisões cadastradas.`
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

  // Filial que a instância editada assume: a atual (se ainda marcada e com setor válido)
  // ou a primeira filial marcada com setores válidos.
  function resolveKeepFilial(): string | undefined {
    const currentKey = editingInstancia ? instanciaFilialKey(editingInstancia) : "";
    const currentStillValid = filialPayloads.find(
      (p) => (p.filial_id ?? "").toLowerCase() === currentKey
    );
    return (currentStillValid ?? filialPayloads[0])?.filial_id;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // Aviso leve quando a mudança de escopo impacta revisões existentes (não bloqueia).
    if (editingInstanciaId && editingHasRevisoes && editingInstancia) {
      const escopoAtual = instanciaFilialKey(editingInstancia);
      const escopoNovo = todasFiliais
        ? "__todas__"
        : (resolveKeepFilial() ?? "").toLowerCase();
      if (escopoNovo !== escopoAtual) {
        const confirmed = window.confirm(
          "Esta instância possui revisões. Alterar o escopo (unidade) reatribui os números ao novo destino e recalcula o dashboard. Deseja continuar?"
        );
        if (!confirmed) return;
      }
    }
    setSaving(true);
    try {
      if (editingInstanciaId) {
        if (todasFiliais) {
          await onUpdate(editingInstanciaId, {
            setor_ids: setorIds,
            rotulo_instancia: rotulo.trim() || undefined,
            status_instancia: statusInstancia,
            todas_filiais_ativas: true,
          });
        } else {
          const keep = resolveKeepFilial();
          const keepPayload = filialPayloads.find(
            (p) => (p.filial_id ?? "").toLowerCase() === (keep ?? "").toLowerCase()
          );
          if (keep && keepPayload) {
            await onUpdate(editingInstanciaId, {
              setor_ids: keepPayload.setor_ids,
              rotulo_instancia: rotulo.trim() || undefined,
              status_instancia: statusInstancia,
              todas_filiais_ativas: false,
              filial_id: keep,
            });
            // Filiais extras marcadas viram novas instâncias (fan-out, igual ao "novo").
            for (const payload of filialPayloads) {
              if ((payload.filial_id ?? "").toLowerCase() === keep.toLowerCase()) continue;
              await onCreate(payload);
            }
          }
        }
      } else if (duplicateSourceId) {
        await onDuplicate({
          origemInstanciaId: duplicateSourceId,
          filial_id: filialId,
          setor_id: setorId,
          rotulo_instancia: rotulo.trim() || undefined,
        });
      } else if (todasFiliais) {
        if (setorIds.length > 0) {
          await onCreate({
            todas_filiais_ativas: true,
            setor_ids: setorIds,
            rotulo_instancia: rotulo.trim() || undefined,
          });
        }
      } else {
        for (const payload of filialPayloads) {
          await onCreate(payload);
        }
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
        header: "Unidade",
        render: (row) =>
          row.todas_filiais_ativas
            ? "Todas as unidades ativas"
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
            <button type="button" className="ds-ghost-btn" onClick={() => startDuplicate(row)}>
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

  // Instâncias extras (novas) que uma edição multi-filial criaria além da editada.
  const editExtraCount = editingInstanciaId && !todasFiliais ? Math.max(0, filialPayloads.length - 1) : 0;

  const submitLabel = saving
    ? "Salvando…"
    : editingInstanciaId
      ? editExtraCount > 0
        ? `Salvar (+${editExtraCount} nova${editExtraCount > 1 ? "s" : ""})`
        : "Salvar alterações"
      : duplicateSourceId
        ? "Replicar timeline"
        : createCount > 1
          ? `Criar ${createCount} instâncias`
          : "Criar instância";

  const canSubmit = editingInstanciaId
    ? todasFiliais
      ? setorIds.length > 0
      : filialPayloads.length > 0
    : duplicateSourceId
      ? Boolean(filialId && setorId)
      : createCount > 0;

  const setoresGrid = (
    <div className="ds-filter-box tm-inst-form__field--full">
      <span className="ds-field-label">Setores *</span>
      <div className="tm-check-grid" role="group" aria-label="Setores da instância">
        {setoresDisponiveis.length === 0 ? (
          <p className="ds-hint">
            {!duplicateSourceId && !todasFiliais && filialIds.length === 0
              ? "Selecione ao menos uma unidade para listar os setores."
              : "Nenhum setor disponível para esta seleção."}
          </p>
        ) : (
          setoresDisponiveis.map((setor) => {
            const { checked, disabled, used } = setorState(setor.id);
            return (
              <label
                key={setor.id}
                className={`tm-check-option${used ? " tm-check-option--used" : ""}`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={disabled}
                  onChange={() => toggleSetor(setor.id)}
                />
                <span>{setor.label}</span>
                {used ? <span className="tm-check-option__tag">em uso</span> : null}
              </label>
            );
          })
        )}
      </div>
    </div>
  );

  const rotuloField = (
    <div className="ds-filter-box tm-inst-form__field--full">
      <label htmlFor="tm-inst-rotulo">Rótulo (opcional)</label>
      <input
        id="tm-inst-rotulo"
        value={rotulo}
        onChange={(e) => setRotulo(e.target.value)}
        placeholder="Ex.: Matriz — rollout Q2"
      />
    </div>
  );

  return (
    <div className="tm-panel-stack">
      <section className="ds-card">
        <div className="ds-table-section__header">
          <div>
            <h2 className="ds-section-title">Instâncias operacionais</h2>
            <p className="ds-hint">
              Cada instância pertence a uma unidade (ou a todas as ativas) e amarra um ou mais
              setores. As revisões ficam na instância.
            </p>
          </div>
          <button type="button" className="ds-primary-btn" disabled={busy} onClick={openCreateForm}>
            <Plus size={16} />
            Nova instância
          </button>
        </div>
        <DataTableSection
          embedded
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
          {isCreate ? (
            <p className="ds-hint">
              Marque uma ou mais unidades e os setores vinculados. Criamos uma instância por unidade;
              setores já usados em uma unidade aparecem desabilitados.
            </p>
          ) : null}
          {editingInstanciaId ? (
            <p className="ds-hint">
              {editingHasRevisoes
                ? "Edição liberada. Trocar a unidade reatribui as revisões ao novo destino e recalcula o dashboard (pediremos confirmação). Unidades extras marcadas criam novas instâncias."
                : "Edite unidades, setores, rótulo e status. A instância assume a unidade marcada; unidades extras criam novas instâncias."}
            </p>
          ) : null}
          {duplicateSourceId ? (
            <p className="ds-hint">
              Replica a timeline (revisões, medições, investimentos e vínculos) para outra unidade e
              setor.
            </p>
          ) : null}
          <form onSubmit={handleSubmit}>
            <div className="tm-inst-form">
              {isCreate ? (
                <>
                  <div className="ds-filter-box ds-filter-box--checkbox">
                    <label className="ds-check-label">
                      <input
                        type="checkbox"
                        checked={todasFiliais}
                        onChange={(e) => {
                          const next = e.target.checked;
                          setTodasFiliais(next);
                          if (!next) {
                            const firstFilial = filialIds[0] ?? options.filiais[0]?.id ?? "01";
                            setSetorIds(defaultSetorIds(options.setores, firstFilial, instancias));
                          }
                        }}
                      />
                      <span>Todas as unidades ativas (instância única consolidada)</span>
                    </label>
                  </div>

                  {!todasFiliais ? (
                    <div className="ds-filter-box tm-inst-form__field--full">
                      <span className="ds-field-label">Unidades *</span>
                      <div className="tm-check-grid" role="group" aria-label="Unidades da instância">
                        {options.filiais.map((filial) => {
                          const checked = filialIds.some(
                            (id) => id.toLowerCase() === filial.id.toLowerCase()
                          );
                          return (
                            <label key={filial.id} className="tm-check-option">
                              <input
                                type="checkbox"
                                checked={checked}
                                onChange={() => toggleFilial(filial.id)}
                              />
                              <span>
                                {filial.id} — {filial.label}
                              </span>
                            </label>
                          );
                        })}
                      </div>
                    </div>
                  ) : null}

                  {setoresGrid}

                  {skippedFiliais.length > 0 ? (
                    <p className="ds-hint">
                      Sem setor livre para: {skippedFiliais.join(", ")}. Essas unidades serão
                      ignoradas.
                    </p>
                  ) : null}

                  {rotuloField}
                </>
              ) : null}

              {editingInstanciaId ? (
                <>
                  <div className="ds-filter-box ds-filter-box--checkbox">
                    <label className="ds-check-label">
                      <input
                        type="checkbox"
                        checked={todasFiliais}
                        onChange={(e) => {
                          const next = e.target.checked;
                          setTodasFiliais(next);
                          if (!next) {
                            const fallback =
                              filialIds[0] || filialId || options.filiais[0]?.id || "01";
                            setFilialIds([fallback]);
                            setSetorIds(defaultSetorIds(options.setores, fallback, instancias));
                          }
                        }}
                      />
                      <span>Todas as unidades ativas (instância consolidada)</span>
                    </label>
                  </div>

                  {!todasFiliais ? (
                    <div className="ds-filter-box tm-inst-form__field--full">
                      <span className="ds-field-label">Unidades *</span>
                      <div className="tm-check-grid" role="group" aria-label="Unidades da instância">
                        {options.filiais.map((filial) => {
                          const checked = filialIds.some(
                            (id) => id.toLowerCase() === filial.id.toLowerCase()
                          );
                          return (
                            <label key={filial.id} className="tm-check-option">
                              <input
                                type="checkbox"
                                checked={checked}
                                onChange={() => toggleFilial(filial.id)}
                              />
                              <span>
                                {filial.id} — {filial.label}
                              </span>
                            </label>
                          );
                        })}
                      </div>
                    </div>
                  ) : null}

                  <div className="tm-inst-form__row">
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
                  </div>

                  {setoresGrid}

                  {skippedFiliais.length > 0 ? (
                    <p className="ds-hint">
                      Sem setor livre para: {skippedFiliais.join(", ")}. Essas unidades serão
                      ignoradas.
                    </p>
                  ) : null}

                  {rotuloField}
                </>
              ) : null}

              {duplicateSourceId ? (
                <>
                  <div className="tm-inst-form__row">
                    <div className="ds-filter-box">
                      <label htmlFor="tm-inst-filial-dup">Unidade destino *</label>
                      <select
                        id="tm-inst-filial-dup"
                        value={filialId}
                        onChange={(e) => {
                          const next = e.target.value;
                          setFilialId(next);
                          setSetorId(resolveSetorIdForFilial(options.setores, next, setorId));
                        }}
                      >
                        {options.filiais.map((filial) => (
                          <option key={filial.id} value={filial.id}>
                            {filial.id} — {filial.label}
                          </option>
                        ))}
                      </select>
                    </div>
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
                  </div>
                  {rotuloField}
                </>
              ) : null}
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
    </div>
  );
}
