import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createKaizenVersion,
  deleteKaizenVersion,
  fetchKaizenRecord,
  fetchKaizenRevisions,
  implementKaizenVersion,
  updateKaizenRecord,
  updateKaizenVersion,
} from "../api/kaizenApi";
import { KaizenPageHeader } from "../components/KaizenPageHeader";
import { StateAlert } from "../components/StateAlert";
import { EditableSectionCard } from "../components/ui/EditableSectionCard";
import { HelpTooltip } from "../components/ui/HelpTooltip";
import { ReadOnlyField } from "../components/ui/ReadOnlyField";
import { KAIZEN_HELP_TOOLTIPS } from "../content/helpTooltips";
import { StatusPipeline } from "../components/detail/StatusPipeline";
import { KaizenEvidencePanel } from "../components/detail/KaizenEvidencePanel";
import { KaizenImprovementsPanel } from "../components/detail/KaizenImprovementsPanel";
import {
  KaizenVersionSwitcher,
  type SelectionMode,
} from "../components/detail/KaizenVersionSwitcher";
import { KaizenChangeLog } from "../components/detail/KaizenChangeLog";
import { KaizenParticipantsField } from "../components/form/KaizenParticipantsField";
import {
  BRANCHES,
  KAIZEN_CATEGORIES,
  KAIZEN_STATUSES,
  SAVINGS_TYPES,
  formValuesToPayload,
  listPath,
  recordToFormValues,
  snapshotToFormValues,
} from "../constants/kaizen";
import type {
  KaizenFormValues,
  KaizenRecord,
  KaizenRevision,
  KaizenVersionStatus,
} from "../types/kaizen";
import { formatCurrency, formatDate } from "../utils/format";
import { savingsTypeLabel } from "../utils/labels";
import { useKaizenSectionEdit } from "../hooks/useKaizenSectionEdit";

type Props = {
  recordId: string;
  onNavigate: (path: string) => void;
};

function versionStatusOf(revision: KaizenRevision | null): KaizenVersionStatus {
  return (revision?.version_status as KaizenVersionStatus) ?? "implantado";
}

const BRANCH_LABEL: Record<string, string> = Object.fromEntries(
  BRANCHES.map((item) => [item.code, item.label]),
);

const ROLE_LABEL: Record<string, string> = {
  responsavel: "Responsável",
  participante: "Participante",
  apoio: "Apoio",
};

function effectivenessLabel(record: KaizenRecord): string {
  const estimated = record.annual_savings;
  const realized = record.realized_annual_savings;
  if (estimated == null || realized == null || estimated === 0) return "—";
  const ratio = Math.round((realized / estimated) * 100);
  return `${ratio}% do estimado`;
}

function savingsAccountingLabel(record: KaizenRecord): string {
  if (!record.date_implemented) return "Sem data de implantação";
  if (record.savings_active) {
    return `Sim, até ${formatDate(record.savings_valid_until)}`;
  }
  return `Não (validade encerrada em ${formatDate(record.savings_valid_until)})`;
}

export function KaizenDetailPage({ recordId, onNavigate }: Props) {
  const [record, setRecord] = useState<KaizenRecord | null>(null);
  const [form, setForm] = useState<KaizenFormValues | null>(null);
  const [revisions, setRevisions] = useState<KaizenRevision[]>([]);
  const [selectedRevision, setSelectedRevision] = useState<number | null>(null);
  const [reloadTick, setReloadTick] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [creating, setCreating] = useState(false);
  const [implementing, setImplementing] = useState(false);
  const [deletingVersion, setDeletingVersion] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [effectiveFrom, setEffectiveFrom] = useState("");
  const [changeReason, setChangeReason] = useState("");

  const { isEditing, startEdit, stopEdit, stopAll } = useKaizenSectionEdit();

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [loaded, revs] = await Promise.all([
        fetchKaizenRecord(recordId),
        fetchKaizenRevisions(recordId).catch(() => [] as KaizenRevision[]),
      ]);
      setRecord(loaded);
      setRevisions(revs);
      setReloadTick((tick) => tick + 1);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar kaizen.");
    } finally {
      setLoading(false);
    }
  }, [recordId]);

  useEffect(() => {
    void load();
  }, [load]);

  const activeRevisionNumber = useMemo(
    () => revisions.find((r) => r.version_status === "implantado")?.revision_number ?? null,
    [revisions],
  );

  // Normaliza a versão selecionada: mantém a atual se ainda existir, senão volta para a ativa.
  useEffect(() => {
    if (!revisions.length) {
      setSelectedRevision(null);
      return;
    }
    setSelectedRevision((current) => {
      if (current != null && revisions.some((r) => r.revision_number === current)) {
        return current;
      }
      return activeRevisionNumber ?? Math.max(...revisions.map((r) => r.revision_number));
    });
  }, [revisions, activeRevisionNumber]);

  const selectedVersion = useMemo(
    () => revisions.find((r) => r.revision_number === selectedRevision) ?? null,
    [revisions, selectedRevision],
  );

  // O card de versões aparece sempre (para o botão "Nova versão"), mas a lista de
  // versões só é exibida quando há mais de uma. Com versão única, a ficha é editada
  // diretamente como correção do cabeçalho (modo "active").
  const hasMultipleVersions = revisions.length > 1;
  const usesSnapshotView =
    hasMultipleVersions && !!selectedVersion && selectedVersion.version_status !== "implantado";

  const selectedStatus = versionStatusOf(selectedVersion);
  const mode: SelectionMode = !hasMultipleVersions
    ? "active"
    : selectedStatus === "implantado"
      ? "active"
      : selectedStatus === "em_andamento"
        ? "draft"
        : "readonly";
  const editable = mode !== "readonly";

  // Deriva o formulário da versão selecionada (rascunho/histórico usam o snapshot).
  useEffect(() => {
    if (!record) return;
    if (usesSnapshotView && selectedVersion) {
      setForm(
        snapshotToFormValues(record, (selectedVersion.snapshot ?? {}) as Partial<KaizenRecord>),
      );
    } else {
      setForm(recordToFormValues(record));
    }
    stopAll();
    setEffectiveFrom("");
    setChangeReason("");
  }, [record, selectedVersion, usesSnapshotView, stopAll]);

  function updateField<K extends keyof KaizenFormValues>(key: K, value: KaizenFormValues[K]) {
    setForm((current) => (current ? { ...current, [key]: value } : current));
  }

  function resetForm() {
    if (!record) return;
    if (usesSnapshotView && selectedVersion) {
      setForm(
        snapshotToFormValues(record, (selectedVersion.snapshot ?? {}) as Partial<KaizenRecord>),
      );
    } else {
      setForm(recordToFormValues(record));
    }
  }

  function cancelSection(key: string) {
    resetForm();
    setEffectiveFrom("");
    setChangeReason("");
    stopEdit(key);
  }

  const saveSection = useCallback(
    async (key: string, withRevisionMeta: boolean) => {
      if (!form || !record) return;
      setSaving(true);
      setError(null);
      setSuccess(null);
      try {
        const payload = formValuesToPayload(form);
        if (mode === "draft" && selectedRevision != null) {
          await updateKaizenVersion(record.id, selectedRevision, payload);
          setSuccess(`Rascunho v${selectedRevision} atualizado.`);
        } else {
          if (withRevisionMeta) {
            if (effectiveFrom) payload.effective_from = effectiveFrom;
            if (changeReason.trim()) payload.change_reason = changeReason.trim();
          }
          await updateKaizenRecord(record.id, payload);
          setSuccess("Correção salva na versão ativa.");
        }
        setEffectiveFrom("");
        setChangeReason("");
        stopEdit(key);
        await load();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao salvar seção.");
      } finally {
        setSaving(false);
      }
    },
    [form, record, mode, selectedRevision, effectiveFrom, changeReason, stopEdit, load],
  );

  const handleCreateVersion = useCallback(async () => {
    if (!record) return;
    setCreating(true);
    setError(null);
    setSuccess(null);
    try {
      const cloned = {
        ...formValuesToPayload(recordToFormValues(record)),
        status: "em_andamento",
      };
      const created = await createKaizenVersion(record.id, cloned);
      await load();
      setSelectedRevision(created.revision_number);
      setSuccess(
        `Versão v${created.revision_number} criada como cópia da ativa. Edite as seções e clique em “Salvar e tornar ativa”.`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar nova versão.");
    } finally {
      setCreating(false);
    }
  }, [record, load]);

  const handleDeleteVersion = useCallback(async () => {
    if (!record || selectedRevision == null || mode === "active") return;
    const confirmed = window.confirm(
      `Excluir a versão v${selectedRevision}? As evidências dessa versão também serão removidas. Esta ação não pode ser desfeita.`,
    );
    if (!confirmed) return;
    setDeletingVersion(true);
    setError(null);
    setSuccess(null);
    const target = selectedRevision;
    try {
      await deleteKaizenVersion(record.id, target);
      setSelectedRevision(null);
      await load();
      setSuccess(`Versão v${target} excluída.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir versão.");
    } finally {
      setDeletingVersion(false);
    }
  }, [record, selectedRevision, mode, load]);

  const handleImplement = useCallback(
    async (effectiveFromDate: string) => {
      if (!record || selectedRevision == null) return;
      setImplementing(true);
      setError(null);
      setSuccess(null);
      const target = selectedRevision;
      try {
        await implementKaizenVersion(record.id, target, { effective_from: effectiveFromDate });
        await load();
        setSelectedRevision(target);
        setSuccess(`Versão v${target} implantada — agora é a versão ativa.`);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao implantar versão.");
      } finally {
        setImplementing(false);
      }
    },
    [record, selectedRevision, load],
  );

  if (loading || !record || !form) {
    return (
      <>
        <KaizenPageHeader
          title="Ficha do kaizen"
          subtitle="Detalhe e edição por seção"
          showBack
          onBack={() => onNavigate(listPath())}
        />
        {error ? <StateAlert variant="error">{error}</StateAlert> : <StateAlert>Carregando ficha…</StateAlert>}
      </>
    );
  }

  const selectedLabel =
    selectedRevision == null
      ? "versão única"
      : !hasMultipleVersions
        ? `versão v${selectedRevision}`
        : `versão v${selectedRevision}${mode === "active" ? " (ativa)" : mode === "draft" ? " (rascunho)" : " (histórico)"}`;

  // Dados exibidos na leitura: cabeçalho para a versão ativa; snapshot para rascunho/histórico.
  const view: KaizenRecord =
    usesSnapshotView && selectedVersion
      ? ({ ...record, ...(selectedVersion.snapshot as Partial<KaizenRecord>), id: record.id } as KaizenRecord)
      : record;
  const viewParticipants =
    mode === "active"
      ? record.participants ?? []
      : view.accountable
        ? [{ name: view.accountable, role: "responsavel" as const }]
        : [];
  const evidenceRevisionId = selectedVersion?.id ?? null;

  return (
    <>
      <KaizenPageHeader
        title={record.title}
        subtitle={`Kaizen • ${BRANCH_LABEL[record.branch_code] ?? record.branch_code} • ${selectedLabel}`}
        showBack
        onBack={() => {
          stopAll();
          onNavigate(listPath());
        }}
      />

      {error ? <StateAlert variant="error">{error}</StateAlert> : null}
      {success ? <StateAlert variant="success">{success}</StateAlert> : null}

      {selectedRevision != null ? (
        <KaizenVersionSwitcher
          revisions={revisions}
          selectedRevision={selectedRevision}
          showList={hasMultipleVersions}
          onSelect={setSelectedRevision}
          onCreateVersion={() => void handleCreateVersion()}
          creating={creating}
          mode={mode}
          onImplement={(date) => void handleImplement(date)}
          implementing={implementing}
          onDelete={() => void handleDeleteVersion()}
          deleting={deletingVersion}
        />
      ) : null}

      {/* Identificação */}
      <EditableSectionCard
        title="Identificação"
        hint={KAIZEN_HELP_TOOLTIPS.sections.identification}
        description="Filial, equipe e descrição do processo"
        isEditing={isEditing("identificacao")}
        onEdit={() => startEdit("identificacao")}
        onCancel={() => cancelSection("identificacao")}
        onSave={() => void saveSection("identificacao", false)}
        saving={saving}
        editable={editable}
        readContent={
          <div className="kz-read-grid">
            <ReadOnlyField label="Filial" value={BRANCH_LABEL[view.branch_code] ?? view.branch_code} />
            <ReadOnlyField label="Setor" value={view.sector} />
            <ReadOnlyField label="Categoria" value={view.category} />
            <ReadOnlyField label="Investimento" value={formatCurrency(view.investment)} />
            <div className="kz-read-field kz-span-2">
              <span className="kz-read-field__label">Equipe / responsáveis</span>
              <div className="kz-chips">
                {viewParticipants.length === 0 ? (
                  <span className="kz-read-field__value kz-read-field__value--empty">—</span>
                ) : (
                  viewParticipants.map((p, index) => (
                    <span key={index} className={`kz-chip kz-chip--${p.role}`}>
                      {p.name}
                      <em>{ROLE_LABEL[p.role] ?? p.role}</em>
                    </span>
                  ))
                )}
              </div>
            </div>
            <ReadOnlyField label="Descrição do processo" value={view.process_description} wide multiline />
            <ReadOnlyField label="Problema / oportunidade" value={view.problem_description} wide multiline />
            <ReadOnlyField label="Melhoria realizada" value={view.improvement_description} wide multiline />
            <ReadOnlyField label="Resultado esperado" value={view.expected_result} wide multiline />
            <ReadOnlyField label="Notas" value={view.notes} wide multiline />
          </div>
        }
        editContent={
          <div className="kz-form-grid">
            <div className="kz-field">
              <label htmlFor="kz-d-branch">Filial *</label>
              <select
                id="kz-d-branch"
                value={form.branch_code}
                onChange={(event) => updateField("branch_code", event.target.value)}
              >
                {BRANCHES.map((item) => (
                  <option key={item.code} value={item.code}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="kz-field">
              <label htmlFor="kz-d-sector">Setor</label>
              <input
                id="kz-d-sector"
                value={form.sector}
                onChange={(event) => updateField("sector", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-d-category">Categoria</label>
              <select
                id="kz-d-category"
                value={form.category}
                onChange={(event) => updateField("category", event.target.value)}
              >
                <option value="">Sem categoria</option>
                {KAIZEN_CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
            <div className="kz-field">
              <label htmlFor="kz-d-investment">Investimento (R$)</label>
              <input
                id="kz-d-investment"
                value={form.investment}
                onChange={(event) => updateField("investment", event.target.value)}
              />
            </div>
            <div className="kz-field kz-span-2">
              <label htmlFor="kz-d-title">Título *</label>
              <input
                id="kz-d-title"
                value={form.title}
                maxLength={500}
                onChange={(event) => updateField("title", event.target.value)}
              />
            </div>
            <div className="kz-field kz-span-2">
              <label>Equipe / responsáveis</label>
              <KaizenParticipantsField
                participants={form.participants}
                onChange={(participants) => updateField("participants", participants)}
              />
            </div>
            <div className="kz-field kz-span-2">
              <label htmlFor="kz-d-process">Descrição do processo</label>
              <textarea
                id="kz-d-process"
                value={form.process_description}
                onChange={(event) => updateField("process_description", event.target.value)}
              />
            </div>
            <div className="kz-field kz-span-2">
              <label htmlFor="kz-d-problem">Problema / oportunidade</label>
              <textarea
                id="kz-d-problem"
                value={form.problem_description}
                onChange={(event) => updateField("problem_description", event.target.value)}
              />
            </div>
            <div className="kz-field kz-span-2">
              <label htmlFor="kz-d-improvement">Melhoria realizada</label>
              <textarea
                id="kz-d-improvement"
                value={form.improvement_description}
                onChange={(event) => updateField("improvement_description", event.target.value)}
              />
            </div>
            <div className="kz-field kz-span-2">
              <label htmlFor="kz-d-expected">Resultado esperado</label>
              <textarea
                id="kz-d-expected"
                value={form.expected_result}
                onChange={(event) => updateField("expected_result", event.target.value)}
              />
            </div>
            <div className="kz-field kz-span-2">
              <label htmlFor="kz-d-notes">Notas</label>
              <textarea
                id="kz-d-notes"
                value={form.notes}
                onChange={(event) => updateField("notes", event.target.value)}
              />
            </div>
          </div>
        }
      />

      {/* Estágio */}
      <EditableSectionCard
        title="Estágio"
        hint={KAIZEN_HELP_TOOLTIPS.sections.stage}
        description="Status operacional da versão vigente (edição = correção, não cria versão)"
        isEditing={isEditing("estagio")}
        onEdit={() => startEdit("estagio")}
        onCancel={() => cancelSection("estagio")}
        onSave={() => void saveSection("estagio", true)}
        saving={saving}
        editable={editable}
        readContent={
          <div className="kz-read-grid">
            <div className="kz-read-field kz-span-2">
              <span className="kz-read-field__label">Situação atual</span>
              <StatusPipeline status={view.status} />
            </div>
            <ReadOnlyField label="Data implantação" value={view.date_implemented} />
            <ReadOnlyField label="Data descontinuação" value={view.date_discontinued} />
          </div>
        }
        editContent={
          <div className="kz-form-grid">
            <div className="kz-field">
              <label htmlFor="kz-d-status">Status</label>
              <select
                id="kz-d-status"
                value={form.status}
                onChange={(event) =>
                  updateField("status", event.target.value as KaizenFormValues["status"])
                }
              >
                {KAIZEN_STATUSES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="kz-field">
              <label htmlFor="kz-d-eff">Vigente a partir de</label>
              <input
                id="kz-d-eff"
                type="date"
                value={effectiveFrom}
                onChange={(event) => setEffectiveFrom(event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-d-date-impl">Data implantação</label>
              <input
                id="kz-d-date-impl"
                type="date"
                value={form.date_implemented}
                onChange={(event) => updateField("date_implemented", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-d-date-disc">Data descontinuação</label>
              <input
                id="kz-d-date-disc"
                type="date"
                value={form.date_discontinued}
                onChange={(event) => updateField("date_discontinued", event.target.value)}
              />
            </div>
            <div className="kz-field kz-span-2">
              <label htmlFor="kz-d-reason">Motivo da correção (registra na auditoria)</label>
              <input
                id="kz-d-reason"
                value={changeReason}
                onChange={(event) => setChangeReason(event.target.value)}
              />
            </div>
          </div>
        }
      />

      {/* Economia */}
      <EditableSectionCard
        title="Economia"
        hint={KAIZEN_HELP_TOOLTIPS.sections.savings}
        description="Parâmetros e economia calculada pela API"
        isEditing={isEditing("economia")}
        onEdit={() => startEdit("economia")}
        onCancel={() => cancelSection("economia")}
        onSave={() => void saveSection("economia", true)}
        saving={saving}
        editable={editable}
        readContent={
          <div className="kz-read-grid">
            <ReadOnlyField label="Tipo de economia" value={savingsTypeLabel(view.savings_type)} />
            <ReadOnlyField label="Estimada / dia" value={formatCurrency(view.daily_savings)} />
            <ReadOnlyField label="Estimada / ano" value={formatCurrency(view.annual_savings)} />
            <ReadOnlyField label="Realizada / dia" value={formatCurrency(view.realized_daily_savings)} />
            <ReadOnlyField label="Realizada / ano" value={formatCurrency(view.realized_annual_savings)} />
            <ReadOnlyField label="Efetividade" value={effectivenessLabel(view)} />
            <ReadOnlyField
              label="Contabiliza ganhos"
              value={savingsAccountingLabel(view)}
              wide
            />
            <ReadOnlyField label="Segundos / ocorrência" value={view.seconds_per_occurrence} />
            <ReadOnlyField label="Ocorrências / dia" value={view.occurrences_per_day} />
            <ReadOnlyField label="Custo hora (R$)" value={view.hourly_cost} />
            <ReadOnlyField label="Qtd. economizada / dia" value={view.quantity_saved_per_day} />
            <ReadOnlyField label="Custo unit. material (R$)" value={view.unit_material_cost} />
            <ReadOnlyField label="Economia fixa / dia (R$)" value={view.fixed_daily_savings} />
          </div>
        }
        editContent={
          <div className="kz-form-grid">
            <div className="kz-field">
              <label htmlFor="kz-d-savings-type">Tipo de economia</label>
              <select
                id="kz-d-savings-type"
                value={form.savings_type}
                onChange={(event) =>
                  updateField("savings_type", event.target.value as KaizenFormValues["savings_type"])
                }
              >
                <option value="">Inferir automaticamente</option>
                {SAVINGS_TYPES.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="kz-field">
              <label htmlFor="kz-d-seconds">Segundos por ocorrência</label>
              <input
                id="kz-d-seconds"
                value={form.seconds_per_occurrence}
                onChange={(event) => updateField("seconds_per_occurrence", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-d-occurrences">Ocorrências por dia</label>
              <input
                id="kz-d-occurrences"
                value={form.occurrences_per_day}
                onChange={(event) => updateField("occurrences_per_day", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-d-hourly">Custo hora (R$)</label>
              <input
                id="kz-d-hourly"
                value={form.hourly_cost}
                onChange={(event) => updateField("hourly_cost", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-d-qty">Quantidade economizada/dia</label>
              <input
                id="kz-d-qty"
                value={form.quantity_saved_per_day}
                onChange={(event) => updateField("quantity_saved_per_day", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-d-unit">Custo unitário material (R$)</label>
              <input
                id="kz-d-unit"
                value={form.unit_material_cost}
                onChange={(event) => updateField("unit_material_cost", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-d-fixed">Economia fixa/dia (R$)</label>
              <input
                id="kz-d-fixed"
                value={form.fixed_daily_savings}
                onChange={(event) => updateField("fixed_daily_savings", event.target.value)}
              />
            </div>
            <div className="kz-field">
              <label htmlFor="kz-d-realized">Economia realizada/dia (R$)</label>
              <input
                id="kz-d-realized"
                value={form.realized_daily_savings}
                onChange={(event) => updateField("realized_daily_savings", event.target.value)}
              />
            </div>
            <div className="kz-field kz-span-2">
              <label htmlFor="kz-d-eco-reason">Motivo da correção (registra na auditoria)</label>
              <input
                id="kz-d-eco-reason"
                value={changeReason}
                onChange={(event) => setChangeReason(event.target.value)}
              />
            </div>
          </div>
        }
      />

      {/* Evidências da versão selecionada */}
      <section className="kz-card kz-section-card">
        <header className="kz-section-card__header">
          <div>
            <h2 className="kz-section-card__title">
              Evidências da versão{selectedRevision != null ? ` v${selectedRevision}` : ""}
              <HelpTooltip
                content={KAIZEN_HELP_TOOLTIPS.sections.evidences}
                ariaLabel="Ajuda: evidências do processo"
              />
            </h2>
            <p className="kz-section-card__desc">
              {mode === "readonly"
                ? "Evidências desta versão histórica (somente leitura)."
                : `Registro visual Antes / Depois e anexos ${
                    mode === "draft" ? "deste rascunho" : "da versão ativa"
                  }. Cada versão tem suas próprias evidências.`}
            </p>
          </div>
        </header>
        <KaizenEvidencePanel
          kaizenId={record.id}
          readOnly={mode === "readonly"}
          revisionId={evidenceRevisionId}
        />
      </section>

      {/* Ganhos e validade */}
      <section className="kz-card kz-section-card">
        <header className="kz-section-card__header">
          <div>
            <h2 className="kz-section-card__title">
              Ganhos e validade
              <HelpTooltip
                content={KAIZEN_HELP_TOOLTIPS.improvements.periodGain}
                ariaLabel="Ajuda: ganhos e validade"
              />
            </h2>
            <p className="kz-section-card__desc">
              Economia ativa hoje e ganho acumulado por período — só a versão implantada
              contabiliza, respeitando a validade de 1 ano.
            </p>
          </div>
        </header>
        <KaizenImprovementsPanel record={record} revisions={revisions} />
      </section>

      {/* Registro de alterações */}
      <section className="kz-card kz-section-card">
        <header className="kz-section-card__header">
          <div>
            <h2 className="kz-section-card__title">
              Registro de alterações
              <HelpTooltip
                content={KAIZEN_HELP_TOOLTIPS.sections.changelog}
                ariaLabel="Ajuda: registro de alterações"
              />
            </h2>
            <p className="kz-section-card__desc">
              Auditoria do kaizen como um todo: linha do tempo, versões e governança.
            </p>
          </div>
        </header>
        <KaizenChangeLog kaizenId={record.id} revisions={revisions} reloadKey={reloadTick} />
      </section>
    </>
  );
}
