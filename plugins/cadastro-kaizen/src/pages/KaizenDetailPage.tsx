import { useCallback, useEffect, useState } from "react";

import { fetchKaizenRecord, fetchKaizenRevisions, updateKaizenRecord } from "../api/kaizenApi";
import { KaizenPageHeader } from "../components/KaizenPageHeader";
import { StateAlert } from "../components/StateAlert";
import { EditableSectionCard } from "../components/ui/EditableSectionCard";
import { ReadOnlyField } from "../components/ui/ReadOnlyField";
import { StatusPipeline } from "../components/detail/StatusPipeline";
import { KaizenEvidencePanel } from "../components/detail/KaizenEvidencePanel";
import { KaizenRevisionTimeline } from "../components/detail/KaizenRevisionTimeline";
import { KaizenParticipantsField } from "../components/form/KaizenParticipantsField";
import {
  BRANCHES,
  KAIZEN_CATEGORIES,
  KAIZEN_STATUSES,
  SAVINGS_TYPES,
  formValuesToPayload,
  listPath,
  recordToFormValues,
} from "../constants/kaizen";
import type { KaizenFormValues, KaizenRecord, KaizenRevision } from "../types/kaizen";
import { formatCurrency } from "../utils/format";
import { savingsTypeLabel, statusLabel } from "../utils/labels";
import { useKaizenSectionEdit } from "../hooks/useKaizenSectionEdit";

type Props = {
  recordId: string;
  onNavigate: (path: string) => void;
};

const BRANCH_LABEL: Record<string, string> = Object.fromEntries(
  BRANCHES.map((item) => [item.code, item.label]),
);

const ROLE_LABEL: Record<string, string> = {
  responsavel: "Responsável",
  participante: "Participante",
  apoio: "Apoio",
};

export function KaizenDetailPage({ recordId, onNavigate }: Props) {
  const [record, setRecord] = useState<KaizenRecord | null>(null);
  const [form, setForm] = useState<KaizenFormValues | null>(null);
  const [revisions, setRevisions] = useState<KaizenRevision[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
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
      setForm(recordToFormValues(loaded));
      setRevisions(revs);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar kaizen.");
    } finally {
      setLoading(false);
    }
  }, [recordId]);

  useEffect(() => {
    void load();
  }, [load]);

  function updateField<K extends keyof KaizenFormValues>(key: K, value: KaizenFormValues[K]) {
    setForm((current) => (current ? { ...current, [key]: value } : current));
  }

  function cancelSection(key: string) {
    if (record) setForm(recordToFormValues(record));
    setEffectiveFrom("");
    setChangeReason("");
    stopEdit(key);
  }

  const saveSection = useCallback(
    async (key: string, withRevisionMeta: boolean) => {
      if (!form) return;
      setSaving(true);
      setError(null);
      setSuccess(null);
      try {
        const payload = formValuesToPayload(form);
        if (withRevisionMeta) {
          if (effectiveFrom) payload.effective_from = effectiveFrom;
          if (changeReason.trim()) payload.change_reason = changeReason.trim();
        }
        await updateKaizenRecord(recordId, payload);
        setSuccess("Seção atualizada com sucesso.");
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
    [form, effectiveFrom, changeReason, recordId, stopEdit, load],
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

  return (
    <>
      <KaizenPageHeader
        title={record.title}
        subtitle={`Kaizen • ${BRANCH_LABEL[record.branch_code] ?? record.branch_code} • revisão v${
          record.current_revision_number ?? 1
        }`}
        showBack
        onBack={() => {
          stopAll();
          onNavigate(listPath());
        }}
      />

      {error ? <StateAlert variant="error">{error}</StateAlert> : null}
      {success ? <StateAlert variant="success">{success}</StateAlert> : null}

      {/* Identificação */}
      <EditableSectionCard
        title="Identificação"
        description="Filial, equipe e descrição do processo"
        isEditing={isEditing("identificacao")}
        onEdit={() => startEdit("identificacao")}
        onCancel={() => cancelSection("identificacao")}
        onSave={() => void saveSection("identificacao", false)}
        saving={saving}
        readContent={
          <div className="kz-read-grid">
            <ReadOnlyField label="Filial" value={BRANCH_LABEL[record.branch_code] ?? record.branch_code} />
            <ReadOnlyField label="Setor" value={record.sector} />
            <ReadOnlyField label="Categoria" value={record.category} />
            <ReadOnlyField label="Investimento" value={formatCurrency(record.investment)} />
            <div className="kz-read-field kz-span-2">
              <span className="kz-read-field__label">Equipe / responsáveis</span>
              <div className="kz-chips">
                {(record.participants ?? []).length === 0 ? (
                  <span className="kz-read-field__value kz-read-field__value--empty">—</span>
                ) : (
                  (record.participants ?? []).map((p, index) => (
                    <span key={index} className={`kz-chip kz-chip--${p.role}`}>
                      {p.name}
                      <em>{ROLE_LABEL[p.role] ?? p.role}</em>
                    </span>
                  ))
                )}
              </div>
            </div>
            <ReadOnlyField label="Descrição do processo" value={record.process_description} wide multiline />
            <ReadOnlyField label="Problema / oportunidade" value={record.problem_description} wide multiline />
            <ReadOnlyField label="Melhoria realizada" value={record.improvement_description} wide multiline />
            <ReadOnlyField label="Resultado esperado" value={record.expected_result} wide multiline />
            <ReadOnlyField label="Notas" value={record.notes} wide multiline />
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
        description="Status operacional do kaizen (gera revisão ao mudar)"
        isEditing={isEditing("estagio")}
        onEdit={() => startEdit("estagio")}
        onCancel={() => cancelSection("estagio")}
        onSave={() => void saveSection("estagio", true)}
        saving={saving}
        readContent={
          <div className="kz-read-grid">
            <div className="kz-read-field kz-span-2">
              <span className="kz-read-field__label">Situação atual</span>
              <StatusPipeline status={record.status} />
            </div>
            <ReadOnlyField label="Data implantação" value={record.date_implemented} />
            <ReadOnlyField label="Data descontinuação" value={record.date_discontinued} />
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
              <label htmlFor="kz-d-reason">Motivo da mudança (registra na revisão)</label>
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
        description="Parâmetros e economia calculada pela API"
        isEditing={isEditing("economia")}
        onEdit={() => startEdit("economia")}
        onCancel={() => cancelSection("economia")}
        onSave={() => void saveSection("economia", true)}
        saving={saving}
        readContent={
          <div className="kz-read-grid">
            <ReadOnlyField label="Tipo de economia" value={savingsTypeLabel(record.savings_type)} />
            <ReadOnlyField label="Economia / dia" value={formatCurrency(record.daily_savings)} />
            <ReadOnlyField label="Economia / ano" value={formatCurrency(record.annual_savings)} />
            <ReadOnlyField label="Segundos / ocorrência" value={record.seconds_per_occurrence} />
            <ReadOnlyField label="Ocorrências / dia" value={record.occurrences_per_day} />
            <ReadOnlyField label="Custo hora (R$)" value={record.hourly_cost} />
            <ReadOnlyField label="Qtd. economizada / dia" value={record.quantity_saved_per_day} />
            <ReadOnlyField label="Custo unit. material (R$)" value={record.unit_material_cost} />
            <ReadOnlyField label="Economia fixa / dia (R$)" value={record.fixed_daily_savings} />
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
            <div className="kz-field kz-span-2">
              <label htmlFor="kz-d-eco-reason">Motivo da mudança (registra na revisão)</label>
              <input
                id="kz-d-eco-reason"
                value={changeReason}
                onChange={(event) => setChangeReason(event.target.value)}
              />
            </div>
          </div>
        }
      />

      {/* Evidências */}
      <section className="kz-card kz-section-card">
        <header className="kz-section-card__header">
          <div>
            <h2 className="kz-section-card__title">Evidências do processo</h2>
            <p className="kz-section-card__desc">Registro visual Antes / Depois e anexos</p>
          </div>
        </header>
        <KaizenEvidencePanel kaizenId={record.id} readOnly={false} />
      </section>

      {/* Revisões */}
      <section className="kz-card kz-section-card">
        <header className="kz-section-card__header">
          <div>
            <h2 className="kz-section-card__title">Revisões</h2>
            <p className="kz-section-card__desc">
              Histórico de versões e mudanças relevantes ({statusLabel(record.status)})
            </p>
          </div>
        </header>
        <KaizenRevisionTimeline revisions={revisions} />
      </section>
    </>
  );
}
