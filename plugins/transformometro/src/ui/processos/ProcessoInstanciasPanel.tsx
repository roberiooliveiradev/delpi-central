import { useEffect, useMemo, useState } from "react";
import { Copy, Plus, Trash2 } from "lucide-react";

import type { DataTableColumn } from "../../components/DataTable";
import { TableRowActions } from "../../components/ui/TableRowActions";
import { DataTableSection } from "../../components/DataTableSection";
import { FieldLabel, HelpTooltip, NativeCheckboxControl, NativeTextControl } from "@delpi/plugin-ui/index";
import { SelectField } from "../../components/ui/SelectField";
import { mapSelectOptions } from "../../components/ui/selectTypes";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import type { OptionsData, ProcessoInstancia } from "../../data/api/transformometroApi";
import { MelhoriaFaseBadge } from "../../components/melhoria/MelhoriaFaseBadge";
import {
  labelMelhoriaPrioridade,
  melhoriaFieldsFromInstancia,
  melhoriaPayloadFromForm,
  MELHORIA_FASE_OPTIONS,
  MELHORIA_PRIORIDADE_OPTIONS,
  type MelhoriaFormFields,
} from "../../constants/melhoriaForm";
import {
  defaultSetorIdsForFilial,
  formatInstanciaSetoresDisplay,
  formatInstanciaUnidadeDisplay,
  hasProcessoEscopo,
  resolveCreateInstanciaEscopo,
  type ProcessoEscopoState,
} from "./processoEscopo";
import { TmNativeTextAreaField } from "../../components/ui/tmNativeFormFields";
import { filterSetoresByFilial } from "../../utils/setores";
import { renderTableStatus } from "../../utils/tablePresentation";
import { DS_GHOST_BTN, dsGhostBtn } from "../../components/ghostChrome";
import { DS_FILTER_BOX_PLAIN, DS_FILTER_BOX_CHECKBOX } from "../../components/filterChrome";

function renderInstanciaUnidade(row: ProcessoInstancia, activeFilialCount: number) {
  if (!row.todas_filiais_ativas) {
    return formatInstanciaUnidadeDisplay(row, activeFilialCount);
  }
  return (
    <span className="tm-instancia-unidade">
      <span className="tm-instancia-unidade__title">Todas as unidades ativas</span>
      <span className="tm-instancia-unidade__badge">Multi-unidade</span>
      {activeFilialCount > 1 ? (
        <span className="tm-instancia-unidade__hint">
          Consolidado: economia e horas × {activeFilialCount} unidades
        </span>
      ) : null}
    </span>
  );
}

function multiplicadorHint(activeFilialCount: number): string {
  const base = TM_HELP_TOOLTIPS.instancias.multiplicadorConsolidado;
  if (activeFilialCount <= 1) return base;
  return `${base} Hoje: ${activeFilialCount} unidades ativas → fator ×${activeFilialCount} no Consolidado.`;
}

type CreatePayload = {
  filial_id?: string;
  todas_filiais_ativas?: boolean;
  setor_ids: string[];
  rotulo_instancia?: string;
} & MelhoriaFormFields;

type Props = {
  instancias: ProcessoInstancia[];
  selectedInstanciaId: string | null;
  options: OptionsData;
  processoEscopo?: ProcessoEscopoState | null;
  busy?: boolean;
  initialShowForm?: boolean;
  /** IDs de instâncias que já possuem revisões (bloqueiam a troca de filial). */
  instanciasComRevisao?: string[];
  /** Quando true, o botão principal navega para a instância (página dedicada). */
  navigateOnSelect?: boolean;
  /** Oculta tabela e botão nova instância (modo embutido na página da instância). */
  hideTable?: boolean;
  /** Abre o formulário de edição desta instância ao montar. */
  initialEditInstanciaId?: string | null;
  /** Chamado ao cancelar edição embutida (ex.: card editável na página da instância). */
  onCancelEdit?: () => void;
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
    } & MelhoriaFormFields
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

export function ProcessoInstanciasPanel({
  instancias,
  selectedInstanciaId,
  options,
  processoEscopo = null,
  busy = false,
  initialShowForm = false,
  instanciasComRevisao = [],
  navigateOnSelect = false,
  hideTable = false,
  initialEditInstanciaId = null,
  onCancelEdit,
  onSelect,
  onCreate,
  onUpdate,
  onDelete,
  onDuplicate,
}: Props) {
  const confirm = useConfirm();
  const processoTemEscopo = hasProcessoEscopo(processoEscopo);
  const initialCreateEscopo = resolveCreateInstanciaEscopo(
    options,
    processoEscopo,
    processoTemEscopo
  );
  const [showForm, setShowForm] = useState(initialShowForm);
  const [editingInstanciaId, setEditingInstanciaId] = useState<string | null>(null);
  const [duplicateSourceId, setDuplicateSourceId] = useState<string | null>(null);
  const [todasFiliais, setTodasFiliais] = useState(initialCreateEscopo.todas_filiais_ativas);
  const [filialId, setFilialId] = useState(initialCreateEscopo.filialId);
  const [filialIds, setFilialIds] = useState<string[]>(initialCreateEscopo.filial_ids);
  const [setorIds, setSetorIds] = useState<string[]>(initialCreateEscopo.setor_ids);
  const [rotulo, setRotulo] = useState("");
  const [statusInstancia, setStatusInstancia] = useState("ativo");
  const [resumoMelhoria, setResumoMelhoria] = useState("");
  const [responsavelLocal, setResponsavelLocal] = useState("");
  const [faseMelhoria, setFaseMelhoria] = useState("planejado");
  const [dataAlvoGoLive, setDataAlvoGoLive] = useState("");
  const [prioridade, setPrioridade] = useState("media");
  const [saving, setSaving] = useState(false);
  const [usarEscopoProcesso, setUsarEscopoProcesso] = useState(processoTemEscopo);

  const editingInstancia = useMemo(
    () => instancias.find((row) => row.instancia_id === editingInstanciaId) ?? null,
    [editingInstanciaId, instancias]
  );

  const isCreate = !editingInstanciaId && !duplicateSourceId;

  const editingHasRevisoes = editingInstanciaId
    ? instanciasComRevisao.some((id) => id === editingInstanciaId)
    : false;

  useEffect(() => {
    if (!initialShowForm) return;
    setShowForm(true);
    // Formulário de criação: herdar escopo do processo na abertura (não só no toggle do checkbox).
    if (editingInstanciaId || duplicateSourceId) return;
    if (!hasProcessoEscopo(processoEscopo) || !processoEscopo) return;
    setUsarEscopoProcesso(true);
    setTodasFiliais(processoEscopo.todas_filiais_ativas);
    setFilialIds(processoEscopo.todas_filiais_ativas ? [] : [...processoEscopo.filial_ids]);
    setSetorIds([...processoEscopo.setor_ids]);
    if (!processoEscopo.todas_filiais_ativas && processoEscopo.filial_ids[0]) {
      setFilialId(processoEscopo.filial_ids[0]);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- só reage à abertura pedida pelo pai
  }, [initialShowForm]);

  // Setores disponíveis conforme o modo (criar/editar multi-filial ou replicar).
  const setoresDisponiveis = useMemo(() => {
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
  }, [todasFiliais, filialIds, options.setores]);

  // Payloads por filial selecionada (novo ou editar); filtra setores válidos/livres por filial.
  const filialPayloads = useMemo<CreatePayload[]>(() => {
    if (duplicateSourceId || todasFiliais) return [];
    const rotuloValue = rotulo.trim() || undefined;
    const payloads: CreatePayload[] = [];
    for (const fid of filialIds) {
      const available = new Set(
        filterSetoresByFilial(options.setores, fid).map((setor) => setor.id.toLowerCase())
      );
      const valid = setorIds.filter((id) => available.has(id.toLowerCase()));
      if (valid.length > 0) {
        payloads.push({
          filial_id: fid,
          todas_filiais_ativas: false,
          setor_ids: valid,
          rotulo_instancia: rotuloValue,
          ...melhoriaPayloadFromForm({
            resumo_melhoria: resumoMelhoria,
            responsavel_local: responsavelLocal,
            fase_melhoria: faseMelhoria,
            data_alvo_go_live: dataAlvoGoLive,
            prioridade,
          }),
        });
      }
    }
    return payloads;
  }, [
    duplicateSourceId,
    rotulo,
    resumoMelhoria,
    responsavelLocal,
    faseMelhoria,
    dataAlvoGoLive,
    prioridade,
    todasFiliais,
    setorIds,
    filialIds,
    options.setores,
  ]);

  // Quantas instâncias o submit produz no modo criar (todas = 1 consolidada).
  const createCount = todasFiliais ? (setorIds.length > 0 ? 1 : 0) : filialPayloads.length;

  // Filiais selecionadas sem departamento marcado (aviso ao usuário).
  const skippedFiliais = useMemo(() => {
    if (duplicateSourceId || todasFiliais) return [] as string[];
    const withPayload = new Set(filialPayloads.map((p) => (p.filial_id ?? "").toLowerCase()));
    return filialIds.filter((fid) => !withPayload.has(fid.toLowerCase()));
  }, [duplicateSourceId, todasFiliais, filialPayloads, filialIds]);

  // Replicar: pares (unidade × setor) válidos — cada par vira uma cópia da timeline.
  const duplicatePayloads = useMemo<{ filial_id: string; setor_id: string }[]>(() => {
    if (!duplicateSourceId) return [];
    const out: { filial_id: string; setor_id: string }[] = [];
    for (const fid of filialIds) {
      const available = new Set(
        filterSetoresByFilial(options.setores, fid).map((setor) => setor.id.toLowerCase())
      );
      for (const sid of setorIds) {
        if (available.has(sid.toLowerCase())) {
          out.push({ filial_id: fid, setor_id: sid });
        }
      }
    }
    return out;
  }, [duplicateSourceId, filialIds, setorIds, options.setores]);

  function resetForm() {
    setShowForm(false);
    setEditingInstanciaId(null);
    setDuplicateSourceId(null);
    setTodasFiliais(false);
    setRotulo("");
    setStatusInstancia("ativo");
    setResumoMelhoria("");
    setResponsavelLocal("");
    setFaseMelhoria("planejado");
    setDataAlvoGoLive("");
    setPrioridade("media");
  }

  function handleCancelForm() {
    resetForm();
    onCancelEdit?.();
  }

  function applyProcessoEscopo() {
    if (!processoEscopo) return;
    const resolved = resolveCreateInstanciaEscopo(options, processoEscopo, true);
    setTodasFiliais(resolved.todas_filiais_ativas);
    setFilialIds(resolved.filial_ids);
    setSetorIds(resolved.setor_ids);
    setFilialId(resolved.filialId);
  }

  function openCreateForm() {
    resetForm();
    const resolved = resolveCreateInstanciaEscopo(options, processoEscopo, processoTemEscopo);
    setFilialId(resolved.filialId);
    setFilialIds(resolved.filial_ids);
    setSetorIds(resolved.setor_ids);
    setTodasFiliais(resolved.todas_filiais_ativas);
    setUsarEscopoProcesso(processoTemEscopo);
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
    const melhoria = melhoriaFieldsFromInstancia(row);
    setResumoMelhoria(melhoria.resumo_melhoria ?? "");
    setResponsavelLocal(melhoria.responsavel_local ?? "");
    setFaseMelhoria(melhoria.fase_melhoria ?? "planejado");
    setDataAlvoGoLive(melhoria.data_alvo_go_live ?? "");
    setPrioridade(melhoria.prioridade ?? "media");
    setShowForm(true);
  }

  useEffect(() => {
    if (!initialEditInstanciaId) return;
    const row = instancias.find((item) => item.instancia_id === initialEditInstanciaId);
    if (row) startEdit(row);
  }, [initialEditInstanciaId, instancias]);

  function startDuplicate(row: ProcessoInstancia) {
    setEditingInstanciaId(null);
    setDuplicateSourceId(row.instancia_id);
    setTodasFiliais(false);
    const filialAtual = row.codigo_filial ?? row.filial_id ?? options.filiais[0]?.id ?? "01";
    setFilialId(filialAtual);
    setFilialIds([filialAtual]);
    setSetorIds([]);
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
        setSetorIds(defaultSetorIdsForFilial(options.setores, next[0]));
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

  function setorState(setorIdValue: string): { checked: boolean; disabled: boolean } {
    const key = setorIdValue.toLowerCase();
    const checked = setorIds.some((id) => id.toLowerCase() === key);
    return { checked, disabled: false };
  }

  async function handleDelete(row: ProcessoInstancia) {
    const confirmed = await confirm({
      title: "Excluir melhoria",
      message: `Excluir melhoria ${row.todas_filiais_ativas ? "todas as unidades" : row.codigo_filial ?? row.filial_id}? Só é possível sem revisões cadastradas.`,
      confirmLabel: "Excluir",
      variant: "danger",
    });
    if (!confirmed) {
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
        const confirmed = await confirm({
          title: "Alterar unidade",
          message:
            "Esta melhoria possui revisões. Alterar a unidade reatribui os números ao novo destino e recalcula o dashboard. Deseja continuar?",
          confirmLabel: "Continuar",
        });
        if (!confirmed) return;
      }
    }
    setSaving(true);
    try {
      const melhoriaPayload = melhoriaPayloadFromForm({
        resumo_melhoria: resumoMelhoria,
        responsavel_local: responsavelLocal,
        fase_melhoria: faseMelhoria,
        data_alvo_go_live: dataAlvoGoLive,
        prioridade,
      });
      if (editingInstanciaId) {
        if (todasFiliais) {
          await onUpdate(editingInstanciaId, {
            setor_ids: setorIds,
            rotulo_instancia: rotulo.trim() || undefined,
            status_instancia: statusInstancia,
            todas_filiais_ativas: true,
            ...melhoriaPayload,
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
              ...melhoriaPayload,
            });
            for (const payload of filialPayloads) {
              if ((payload.filial_id ?? "").toLowerCase() === keep.toLowerCase()) continue;
              await onCreate(payload);
            }
          }
        }
      } else if (duplicateSourceId) {
        for (const pair of duplicatePayloads) {
          await onDuplicate({
            origemInstanciaId: duplicateSourceId,
            filial_id: pair.filial_id,
            setor_id: pair.setor_id,
            rotulo_instancia: rotulo.trim() || undefined,
          });
        }
      } else if (todasFiliais) {
        if (setorIds.length > 0) {
          await onCreate({
            todas_filiais_ativas: true,
            setor_ids: setorIds,
            rotulo_instancia: rotulo.trim() || undefined,
            ...melhoriaPayload,
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

  const activeFilialCount = options.filiais.length;

  const columns = useMemo<DataTableColumn<ProcessoInstancia>[]>(
    () => [
      {
        key: "filial",
        header: "Unidade",
        headerHint: TM_HELP_TOOLTIPS.instancias.colunaUnidade,
        render: (row) => renderInstanciaUnidade(row, activeFilialCount),
      },
      {
        key: "status",
        header: "Status",
        headerHint: TM_HELP_TOOLTIPS.instancias.status,
        render: (row) => row.status_instancia ? renderTableStatus(row.status_instancia) : renderTableStatus("ativo"),
      },
      {
        key: "setor",
        header: "Departamentos",
        headerHint: TM_HELP_TOOLTIPS.instancias.setores,
        render: (row) => formatInstanciaSetoresDisplay(row),
      },
      {
        key: "rotulo",
        header: "Título",
        headerHint: TM_HELP_TOOLTIPS.instancias.rotulo,
        render: (row) => row.rotulo_instancia ?? "—",
      },
      {
        key: "fase",
        header: "Fase",
        headerHint: TM_HELP_TOOLTIPS.instancias.fase,
        render: (row) => <MelhoriaFaseBadge fase={row.fase_melhoria} />,
      },
      {
        key: "prioridade",
        header: "Prioridade",
        headerHint: TM_HELP_TOOLTIPS.instancias.prioridade,
        render: (row) => labelMelhoriaPrioridade(row.prioridade),
      },
      {
        key: "acoes",
        header: "Ações",
        headerHint: TM_HELP_TOOLTIPS.columns.acoes,
        className: "ds-table__actions-col ds-table__actions-col--wide",
        render: (row) => (
          <TableRowActions>
            <button
              type="button"
              className={!navigateOnSelect && selectedInstanciaId === row.instancia_id ? dsGhostBtn("active") : DS_GHOST_BTN}
              onClick={() => onSelect(row.instancia_id)}
            >
              {navigateOnSelect
                ? "Abrir"
                : selectedInstanciaId === row.instancia_id
                  ? "Selecionada"
                  : "Selecionar"}
            </button>
            <button type="button" className={DS_GHOST_BTN} onClick={() => startDuplicate(row)}>
              <Copy size={14} />
              Replicar
            </button>
            <button
              type="button"
              className={dsGhostBtn('danger')}
              disabled={busy || saving}
              onClick={() => void handleDelete(row)}
            >
              <Trash2 size={14} />
              Excluir
            </button>
          </TableRowActions>
        ),
      },
    ],
    [activeFilialCount, busy, navigateOnSelect, onSelect, saving, selectedInstanciaId]
  );

  const formTitle = editingInstanciaId
    ? "Editar melhoria"
    : duplicateSourceId
      ? "Replicar melhoria"
      : "Nova melhoria";

  // Instâncias extras (novas) que uma edição multi-filial criaria além da editada.
  const editExtraCount = editingInstanciaId && !todasFiliais ? Math.max(0, filialPayloads.length - 1) : 0;

  const submitLabel = saving
    ? "Salvando…"
    : editingInstanciaId
      ? editExtraCount > 0
        ? `Salvar (+${editExtraCount} nova${editExtraCount > 1 ? "s" : ""})`
        : "Salvar alterações"
      : duplicateSourceId
        ? duplicatePayloads.length > 1
          ? `Replicar ${duplicatePayloads.length} cópias`
          : "Replicar timeline"
        : createCount > 1
          ? `Criar ${createCount} melhorias`
          : "Criar melhoria";

  const canSubmit = editingInstanciaId
    ? todasFiliais
      ? setorIds.length > 0
      : filialPayloads.length > 0
    : duplicateSourceId
      ? duplicatePayloads.length > 0
      : createCount > 0;

  const unidadesGrid = (
    <div className={`${DS_FILTER_BOX_PLAIN} tm-inst-form__field--full`}>
      <span className="ds-field-label">
        <FieldLabel className="tm-field__label" label="Unidades *" hint={TM_HELP_TOOLTIPS.instancias.unidades} />
      </span>
      <div className="tm-check-grid" role="group" aria-label="Unidades da melhoria">
        {options.filiais.map((filial) => {
          const checked = filialIds.some(
            (id) => id.toLowerCase() === filial.id.toLowerCase()
          );
          return (
            <NativeCheckboxControl key={filial.id} className="tm-check-option" checked={checked} onChange={() => toggleFilial(filial.id)} label={filial.label} />
          );
        })}
      </div>
    </div>
  );

  const setoresGrid = (
    <div className={`${DS_FILTER_BOX_PLAIN} tm-inst-form__field--full`}>
      <span className="ds-field-label">
        <FieldLabel className="tm-field__label" label="Departamentos *" hint={TM_HELP_TOOLTIPS.instancias.setores} />
      </span>
      <div className="tm-check-grid" role="group" aria-label="Departamentos da melhoria">
        {setoresDisponiveis.length === 0 ? (
          <p className="ds-hint">
            {!duplicateSourceId && !todasFiliais && filialIds.length === 0
              ? "Selecione ao menos uma unidade para listar os departamentos."
              : "Nenhum departamento disponível para esta seleção."}
          </p>
        ) : (
          setoresDisponiveis.map((setor) => {
            const { checked, disabled } = setorState(setor.id);
            return (
              <NativeCheckboxControl key={setor.id} className="tm-check-option" checked={checked} disabled={disabled} onChange={() => toggleSetor(setor.id)} label={setor.label} />
            );
          })
        )}
      </div>
    </div>
  );

  const melhoriaFields = (
    <>
      <TmNativeTextAreaField
        id="tm-melhoria-resumo"
        label="Resumo da melhoria"
        hint={TM_HELP_TOOLTIPS.instancias.resumo}
        span
        rows={3}
        value={resumoMelhoria}
        placeholder="Ex.: Automatizar emissão de laudos na recepção de materiais"
        onChange={setResumoMelhoria}
      />
      <div className="tm-inst-form__row">
        <div className={DS_FILTER_BOX_PLAIN}>
          <label htmlFor="tm-melhoria-responsavel">
            <FieldLabel className="tm-field__label" label="Responsável local" hint={TM_HELP_TOOLTIPS.instancias.responsavel} />
          </label>
          <NativeTextControl
            id="tm-melhoria-responsavel"
            value={responsavelLocal}
            onChange={setResponsavelLocal}
            placeholder="Nome do gestor ou patrocinador"
          />
        </div>
        <SelectField
          id="tm-melhoria-fase"
          label="Fase"
          hint={TM_HELP_TOOLTIPS.instancias.fase}
          value={faseMelhoria}
          onChange={setFaseMelhoria}
          options={MELHORIA_FASE_OPTIONS}
        />
      </div>
      <div className="tm-inst-form__row">
        <div className={DS_FILTER_BOX_PLAIN}>
          <label htmlFor="tm-melhoria-data-alvo">
            <FieldLabel className="tm-field__label" label="Data-alvo de go-live" hint={TM_HELP_TOOLTIPS.instancias.dataAlvo} />
          </label>
          <NativeTextControl
            id="tm-melhoria-data-alvo"
            type="date"
            value={dataAlvoGoLive}
          onChange={setDataAlvoGoLive}
          />
        </div>
        <SelectField
          id="tm-melhoria-prioridade"
          label="Prioridade"
          hint={TM_HELP_TOOLTIPS.instancias.prioridade}
          value={prioridade}
          onChange={setPrioridade}
          options={MELHORIA_PRIORIDADE_OPTIONS}
        />
      </div>
    </>
  );

  const rotuloField = (
    <div className={`${DS_FILTER_BOX_PLAIN} tm-inst-form__field--full`}>
      <label htmlFor="tm-inst-rotulo">
        <FieldLabel className="tm-field__label" label="Título (opcional)" hint={TM_HELP_TOOLTIPS.instancias.rotulo} />
      </label>
      <NativeTextControl
        id="tm-inst-rotulo"
        value={rotulo}
        onChange={setRotulo}
        placeholder="Ex.: Automação do fechamento — Q2/2026"
      />
    </div>
  );

  return (
    <div className="tm-panel-stack">
      {hideTable ? null : (
      <section className="ds-card">
        <div className="ds-table-section__header">
          <div>
            <h2 className="ds-section-title">
              <span className="ds-field-label">
                Melhorias
                <HelpTooltip
                  content={TM_HELP_TOOLTIPS.instancias.escopo}
                  ariaLabel="Ajuda: Melhorias"
                />
              </span>
            </h2>
            <p className="ds-hint">
              Cada melhoria aplica o processo a unidades e departamentos — podem se repetir livremente.
              Abra para definir escopo, baseline, cenários e medições.
            </p>
          </div>
          <button type="button" className="ds-primary-btn" disabled={busy} onClick={openCreateForm}>
            <Plus size={16} />
            Nova melhoria
          </button>
        </div>
        <DataTableSection
          embedded
          title=""
          columns={columns}
          rows={instancias}
          rowKey={(row) => row.instancia_id}
          hideSearch
          emptyMessage="Nenhuma melhoria cadastrada."
        />
      </section>
      )}

      {showForm ? (
        <section className="ds-card ds-cadastro-form">
          <h2 className="ds-section-title">{formTitle}</h2>
          {isCreate ? (
            <p className="ds-hint">
              Marque unidades e departamentos. Várias melhorias podem usar a mesma combinação — cada
              cadastro representa um foco distinto de transformação no processo.
            </p>
          ) : null}
          {editingInstanciaId ? (
            <p className="ds-hint">
              {editingHasRevisoes
                ? "Edição liberada. Trocar a unidade reatribui as revisões ao novo destino (pediremos confirmação). Unidades extras criam novas melhorias."
                : "Edite unidades, departamentos, título, fase e status. Unidades extras criam novas melhorias."}
            </p>
          ) : null}
          {duplicateSourceId ? (
            <p className="ds-hint">
              Replica a timeline (revisões, medições, investimentos e vínculos). Marque unidades e
              departamentos de destino — cada par válido vira uma nova melhoria.
            </p>
          ) : null}
          <form onSubmit={handleSubmit}>
            <div className="tm-inst-form">
              {isCreate ? (
                <>
                  {processoTemEscopo ? (
                    <div className={`${DS_FILTER_BOX_CHECKBOX} tm-inst-form__field--full`}>
                      <NativeCheckboxControl
                        className="ds-check-label"
                        checked={usarEscopoProcesso}
                        onChange={(next) => {
                            setUsarEscopoProcesso(next);
                            if (next) {
                              applyProcessoEscopo();
                            }
                        }}
                        label="Usar unidades e departamentos do processo"
                      />
                    </div>
                  ) : null}

                  {!usarEscopoProcesso || !processoTemEscopo ? (
                    <>
                      <div className={DS_FILTER_BOX_CHECKBOX}>
                        <NativeCheckboxControl
                          className="ds-check-label"
                          checked={todasFiliais}
                          onChange={(next) => {
                              setTodasFiliais(next);
                              if (!next) {
                                const firstFilial = filialIds[0] ?? options.filiais[0]?.id ?? "01";
                                setSetorIds(defaultSetorIdsForFilial(options.setores, firstFilial));
                              }
                            }}
                          label={<><span>Todas as unidades ativas (melhoria multi-unidade)</span><HelpTooltip
                            content={multiplicadorHint(activeFilialCount)}
                            ariaLabel="Ajuda: Instância multi-unidade"
                          /></>}
                        />
                      </div>

                      {todasFiliais ? (
                        <p className="tm-instancia-multi-banner">{multiplicadorHint(activeFilialCount)}</p>
                      ) : null}

                      {!todasFiliais ? unidadesGrid : null}

                      {setoresGrid}
                    </>
                  ) : (
                    <>
                      <p className="ds-hint">
                        Escopo herdado do processo-mestre. Desmarque acima para escolher outras
                        unidades ou departamentos nesta melhoria.
                      </p>
                      {todasFiliais ? (
                        <p className="tm-instancia-multi-banner">{multiplicadorHint(activeFilialCount)}</p>
                      ) : (
                        <p className="ds-hint">
                          Unidades:{" "}
                          {filialIds
                            .map((id) => options.filiais.find((filial) => filial.id === id)?.label ?? id)
                            .join("; ") || "—"}
                        </p>
                      )}
                      <p className="ds-hint">
                        Departamentos:{" "}
                        {setorIds
                          .map((id) => options.setores.find((setor) => setor.id === id)?.label ?? id)
                          .join("; ") || "—"}
                      </p>
                    </>
                  )}

                  {skippedFiliais.length > 0 ? (
                    <p className="ds-hint">
                      Sem departamento selecionado para: {skippedFiliais.join(", ")}. Essas unidades serão
                      ignoradas.
                    </p>
                  ) : null}

                  {melhoriaFields}
                  {rotuloField}
                </>
              ) : null}

              {editingInstanciaId ? (
                <>
                  <div className={DS_FILTER_BOX_CHECKBOX}>
                    <NativeCheckboxControl
                      className="ds-check-label"
                      checked={todasFiliais}
                      onChange={(next) => {
                          setTodasFiliais(next);
                          if (!next) {
                            const fallback =
                              filialIds[0] || filialId || options.filiais[0]?.id || "01";
                            setFilialIds([fallback]);
                            setSetorIds(defaultSetorIdsForFilial(options.setores, fallback));
                          }
                        }}
                      label={<><span>Todas as unidades ativas (melhoria multi-unidade)</span><HelpTooltip
                        content={multiplicadorHint(activeFilialCount)}
                        ariaLabel="Ajuda: Instância multi-unidade"
                      /></>}
                    />
                  </div>

                  {todasFiliais ? (
                    <p className="tm-instancia-multi-banner">{multiplicadorHint(activeFilialCount)}</p>
                  ) : null}

                  {!todasFiliais ? unidadesGrid : null}

                  <div className="tm-inst-form__row">
                    <SelectField
                      id="tm-inst-status"
                      label="Status *"
                      hint={TM_HELP_TOOLTIPS.instancias.status}
                      value={statusInstancia}
                      onChange={setStatusInstancia}
                      options={mapSelectOptions(["ativo", "inativo"])}
                    />
                  </div>

                  {setoresGrid}

                  {skippedFiliais.length > 0 ? (
                    <p className="ds-hint">
                      Sem departamento selecionado para: {skippedFiliais.join(", ")}. Essas unidades serão
                      ignoradas.
                    </p>
                  ) : null}

                  {melhoriaFields}
                  {rotuloField}
                </>
              ) : null}

              {duplicateSourceId ? (
                <>
                  {unidadesGrid}

                  {setoresGrid}

                  {melhoriaFields}
                  {rotuloField}
                </>
              ) : null}
            </div>
            <div className="ds-cadastro-form__actions">
              <button type="submit" className="ds-primary-btn" disabled={saving || !canSubmit}>
                {submitLabel}
              </button>
              <button type="button" className={DS_GHOST_BTN} disabled={saving} onClick={handleCancelForm}>
                Cancelar
              </button>
            </div>
          </form>
        </section>
      ) : null}
    </div>
  );
}
