import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { valuesEqual } from "@delpi/plugin-ui/index";

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
import {
  CategoryMultiSelectField,
  KaizenFormProgress,
  KaizenParticipantsField,
  SavingsParamFields,
  SavingsParamReadFields,
} from "../components/form";
import {
  KaizenChangeLog,
  KaizenEvidencePanel,
  KaizenImprovementsPanel,
  KaizenVersionSwitcher,
  StatusPipeline,
  type SelectionMode,
} from "../components/detail";
import {
  DateField,
  EditableSectionCard,
  FormFieldShell,
  FormGrid,
  ReadOnlyChipsField,
  ReadOnlyField,
  ReadOnlyGrid,
  SectionCard,
  SelectField,
  StateAlert,
  TextAreaField,
  TextField,
} from "../components/ui";
import { KAIZEN_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  BRANCHES,
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
import { categoriesFromRecord } from "../utils/kaizenCategories";
import { savingsTypeLabel } from "../utils/labels";
import { validateKaizenFormStatusDates } from "../utils/validateKaizenStatusDates";
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

const BRANCH_OPTIONS = BRANCHES.map((item) => ({ value: item.code, label: item.label }));

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
  const [changeReason, setChangeReason] = useState("");

  const formEditBaselineRef = useRef<KaizenFormValues | null>(null);
  const changeReasonEditBaselineRef = useRef("");

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
      : selectedStatus === "recebido"
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
    setChangeReason("");
    formEditBaselineRef.current = null;
    changeReasonEditBaselineRef.current = "";
  }, [record, selectedVersion, usesSnapshotView, stopAll]);

  function beginSectionEdit(sectionKey: string) {
    if (form) {
      formEditBaselineRef.current = structuredClone(form);
    }
    changeReasonEditBaselineRef.current = changeReason;
    startEdit(sectionKey);
  }

  function sectionFormDirty(includeChangeReason: boolean): boolean {
    const baseline = formEditBaselineRef.current;
    if (!form || !baseline) return false;
    if (!valuesEqual(form, baseline)) return true;
    return includeChangeReason && changeReason !== changeReasonEditBaselineRef.current;
  }

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
    if (formEditBaselineRef.current) {
      setForm(structuredClone(formEditBaselineRef.current));
    } else {
      resetForm();
    }
    setChangeReason(changeReasonEditBaselineRef.current);
    stopEdit(key);
  }

  const saveSection = useCallback(
    async (key: string, withRevisionMeta: boolean) => {
      if (!form || !record) return;
      setSaving(true);
      setError(null);
      setSuccess(null);
      try {
        const statusDateError = validateKaizenFormStatusDates(form);
        if (statusDateError) {
          throw new Error(statusDateError);
        }
        const payload = formValuesToPayload(form);
        if (mode === "draft" && selectedRevision != null) {
          await updateKaizenVersion(record.id, selectedRevision, payload);
          setSuccess(`Rascunho v${selectedRevision} atualizado.`);
        } else {
          if (withRevisionMeta && changeReason.trim()) {
            payload.change_reason = changeReason.trim();
          }
          await updateKaizenRecord(record.id, payload);
          setSuccess("Correção salva na versão ativa.");
        }
        setChangeReason("");
        stopEdit(key);
        await load();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao salvar seção.");
      } finally {
        setSaving(false);
      }
    },
    [form, record, mode, selectedRevision, changeReason, stopEdit, load],
  );

  const handleCreateVersion = useCallback(async () => {
    if (!record) return;
    setCreating(true);
    setError(null);
    setSuccess(null);
    try {
      const cloned = {
        ...formValuesToPayload(recordToFormValues(record)),
        status: "recebido",
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

  const handleImplement = useCallback(async () => {
      if (!record || selectedRevision == null || !form) return;
      setImplementing(true);
      setError(null);
      setSuccess(null);
      const target = selectedRevision;
      try {
        await updateKaizenVersion(record.id, target, formValuesToPayload(form));
        await implementKaizenVersion(record.id, target);
        await load();
        setSelectedRevision(target);
        setSuccess(`Versão v${target} implantada — agora é a versão ativa.`);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao implantar versão.");
      } finally {
        setImplementing(false);
      }
    },
    [record, selectedRevision, form, load],
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
          onImplement={() => void handleImplement()}
          implementing={implementing}
          onDelete={() => void handleDeleteVersion()}
          deleting={deletingVersion}
        />
      ) : null}

      <KaizenFormProgress
        values={recordToFormValues(view)}
        title={`Preenchimento ${selectedLabel !== "versão única" ? `da ${selectedLabel}` : "do processo"}`}
      />

      {/* Identificação */}
      <EditableSectionCard
        title="Identificação"
        hint={KAIZEN_HELP_TOOLTIPS.sections.identification}
        description="Unidade, equipe e descrição do processo"
        isEditing={isEditing("identificacao")}
        onEdit={() => beginSectionEdit("identificacao")}
        onCancel={() => cancelSection("identificacao")}
        onSave={() => void saveSection("identificacao", false)}
        saving={saving}
        dirty={sectionFormDirty(false)}
        editable={editable}
        readContent={
          <ReadOnlyGrid>
            <ReadOnlyField
              label="Unidade"
              hint={KAIZEN_HELP_TOOLTIPS.fields.branch}
              value={BRANCH_LABEL[view.branch_code] ?? view.branch_code}
            />
            <ReadOnlyField label="Setor" hint={KAIZEN_HELP_TOOLTIPS.fields.sector} value={view.sector} />
            <ReadOnlyChipsField
              label="Categoria"
              hint={KAIZEN_HELP_TOOLTIPS.fields.category}
              items={categoriesFromRecord(view)}
              renderChip={(category) => (
                <span key={category} className="kz-chip">
                  {category}
                </span>
              )}
            />
            <ReadOnlyField
              label="Investimento"
              hint={KAIZEN_HELP_TOOLTIPS.fields.investment}
              value={formatCurrency(view.investment)}
            />
            <ReadOnlyChipsField
              label="Equipe / responsáveis"
              hint={KAIZEN_HELP_TOOLTIPS.sections.participants}
              wide
              items={viewParticipants}
              renderChip={(participant, index) => (
                <span key={index} className={`kz-chip kz-chip--${participant.role}`}>
                  {participant.name}
                  <em>{ROLE_LABEL[participant.role] ?? participant.role}</em>
                </span>
              )}
            />
            <ReadOnlyField
              label="Descrição do processo"
              hint={KAIZEN_HELP_TOOLTIPS.fields.processDescription}
              value={view.process_description}
              wide
              multiline
            />
            <ReadOnlyField
              label="Problema / oportunidade"
              hint={KAIZEN_HELP_TOOLTIPS.fields.problemDescription}
              value={view.problem_description}
              wide
              multiline
            />
            <ReadOnlyField
              label="Melhoria realizada"
              hint={KAIZEN_HELP_TOOLTIPS.fields.improvementDescription}
              value={view.improvement_description}
              wide
              multiline
            />
            <ReadOnlyField
              label="Resultado esperado"
              hint={KAIZEN_HELP_TOOLTIPS.fields.expectedResult}
              value={view.expected_result}
              wide
              multiline
            />
            <ReadOnlyField
              label="Notas"
              hint={KAIZEN_HELP_TOOLTIPS.fields.notes}
              value={view.notes}
              wide
              multiline
            />
          </ReadOnlyGrid>
        }
        editContent={
          <FormGrid>
            <SelectField
              id="kz-d-branch"
              label="Unidade *"
              hint={KAIZEN_HELP_TOOLTIPS.fields.branch}
              required
              value={form.branch_code}
              onChange={(value) => updateField("branch_code", value)}
              options={BRANCH_OPTIONS}
            />
            <TextField
              id="kz-d-sector"
              label="Setor"
              hint={KAIZEN_HELP_TOOLTIPS.fields.sector}
              value={form.sector}
              onChange={(value) => updateField("sector", value)}
            />
            <CategoryMultiSelectField
              className="kz-field--multi-select"
              selectedValues={form.categories}
              onChange={(categories) => updateField("categories", categories)}
            />
            <TextField
              id="kz-d-investment"
              label="Investimento (R$)"
              hint={KAIZEN_HELP_TOOLTIPS.fields.investment}
              inputMode="decimal"
              value={form.investment}
              onChange={(value) => updateField("investment", value)}
            />
            <TextField
              id="kz-d-title"
              label="Título *"
              hint={KAIZEN_HELP_TOOLTIPS.fields.title}
              span
              required
              maxLength={500}
              value={form.title}
              onChange={(value) => updateField("title", value)}
            />
            <FormFieldShell
              id="kz-d-participants"
              label="Equipe / responsáveis"
              hint={KAIZEN_HELP_TOOLTIPS.sections.participants}
              span
            >
              <KaizenParticipantsField
                participants={form.participants}
                onChange={(participants) => updateField("participants", participants)}
              />
            </FormFieldShell>
            <TextAreaField
              id="kz-d-process"
              label="Descrição do processo"
              hint={KAIZEN_HELP_TOOLTIPS.fields.processDescription}
              span
              value={form.process_description}
              onChange={(value) => updateField("process_description", value)}
            />
            <TextAreaField
              id="kz-d-problem"
              label="Problema / oportunidade"
              hint={KAIZEN_HELP_TOOLTIPS.fields.problemDescription}
              span
              value={form.problem_description}
              onChange={(value) => updateField("problem_description", value)}
            />
            <TextAreaField
              id="kz-d-improvement"
              label="Melhoria realizada"
              hint={KAIZEN_HELP_TOOLTIPS.fields.improvementDescription}
              span
              value={form.improvement_description}
              onChange={(value) => updateField("improvement_description", value)}
            />
            <TextAreaField
              id="kz-d-expected"
              label="Resultado esperado"
              hint={KAIZEN_HELP_TOOLTIPS.fields.expectedResult}
              span
              value={form.expected_result}
              onChange={(value) => updateField("expected_result", value)}
            />
            <TextAreaField
              id="kz-d-notes"
              label="Notas"
              hint={KAIZEN_HELP_TOOLTIPS.fields.notes}
              span
              value={form.notes}
              onChange={(value) => updateField("notes", value)}
            />
          </FormGrid>
        }
      />

      {/* Estágio */}
      <EditableSectionCard
        title="Estágio"
        hint={KAIZEN_HELP_TOOLTIPS.sections.stage}
        description="Status operacional da versão vigente (edição = correção, não cria versão)"
        isEditing={isEditing("estagio")}
        onEdit={() => beginSectionEdit("estagio")}
        onCancel={() => cancelSection("estagio")}
        onSave={() => void saveSection("estagio", true)}
        saving={saving}
        dirty={sectionFormDirty(true)}
        editable={editable}
        readContent={
          <ReadOnlyGrid>
            <ReadOnlyField
              label="Situação atual"
              wide
              value={<StatusPipeline status={view.status} />}
            />
            <ReadOnlyField
              label="Recebimento da ideia"
              hint={KAIZEN_HELP_TOOLTIPS.fields.dateIdeaReceived}
              value={formatDate(view.date_idea_received)}
            />
            <ReadOnlyField
              label="Data aprovação no comitê"
              hint={KAIZEN_HELP_TOOLTIPS.fields.dateCommitteeApproved}
              value={formatDate(view.date_committee_approved)}
            />
            <ReadOnlyField
              label="Data implantação"
              hint={KAIZEN_HELP_TOOLTIPS.fields.dateImplemented}
              value={formatDate(view.date_implemented)}
            />
            <ReadOnlyField
              label="Data descontinuação"
              hint={KAIZEN_HELP_TOOLTIPS.fields.dateDiscontinued}
              value={formatDate(view.date_discontinued)}
            />
          </ReadOnlyGrid>
        }
        editContent={
          <FormGrid>
            <SelectField
              id="kz-d-status"
              label="Status"
              hint={KAIZEN_HELP_TOOLTIPS.fields.status}
              value={form.status}
              onChange={(value) => updateField("status", value as KaizenFormValues["status"])}
              options={KAIZEN_STATUSES}
            />
            <DateField
              id="kz-d-date-idea"
              label="Recebimento da ideia"
              hint={KAIZEN_HELP_TOOLTIPS.fields.dateIdeaReceived}
              value={form.date_idea_received}
              onChange={(value) => updateField("date_idea_received", value)}
            />
            <DateField
              id="kz-d-date-committee"
              label={
                form.status === "aprovado"
                  ? "Data aprovação no comitê *"
                  : "Data aprovação no comitê"
              }
              hint={KAIZEN_HELP_TOOLTIPS.fields.dateCommitteeApproved}
              required={form.status === "aprovado"}
              value={form.date_committee_approved}
              onChange={(value) => updateField("date_committee_approved", value)}
            />
            <DateField
              id="kz-d-date-impl"
              label={form.status === "implantado" ? "Data implantação *" : "Data implantação"}
              hint={KAIZEN_HELP_TOOLTIPS.fields.dateImplemented}
              required={form.status === "implantado"}
              value={form.date_implemented}
              onChange={(value) => updateField("date_implemented", value)}
            />
            <DateField
              id="kz-d-date-disc"
              label="Data descontinuação"
              hint={KAIZEN_HELP_TOOLTIPS.fields.dateDiscontinued}
              value={form.date_discontinued}
              onChange={(value) => updateField("date_discontinued", value)}
            />
            <TextField
              id="kz-d-reason"
              label="Motivo da correção (registra na auditoria)"
              hint={KAIZEN_HELP_TOOLTIPS.fields.changeReason}
              span
              value={changeReason}
              onChange={setChangeReason}
            />
          </FormGrid>
        }
      />

      {/* Economia */}
      <EditableSectionCard
        title="Economia"
        hint={KAIZEN_HELP_TOOLTIPS.sections.savings}
        description="Parâmetros e economia calculada pela API"
        isEditing={isEditing("economia")}
        onEdit={() => beginSectionEdit("economia")}
        onCancel={() => cancelSection("economia")}
        onSave={() => void saveSection("economia", true)}
        saving={saving}
        dirty={sectionFormDirty(true)}
        editable={editable}
        readContent={
          <ReadOnlyGrid>
            <ReadOnlyField
              label="Tipo de economia"
              hint={KAIZEN_HELP_TOOLTIPS.fields.savingsType}
              value={savingsTypeLabel(view.savings_type)}
            />
            <ReadOnlyField
              label="Estimada / dia"
              hint={KAIZEN_HELP_TOOLTIPS.fields.estimatedDaily}
              value={formatCurrency(view.daily_savings)}
            />
            <ReadOnlyField
              label="Estimada / ano"
              hint={KAIZEN_HELP_TOOLTIPS.fields.estimatedAnnual}
              value={formatCurrency(view.annual_savings)}
            />
            <ReadOnlyField
              label="Realizada / dia"
              hint={KAIZEN_HELP_TOOLTIPS.fields.realizedDailySavings}
              value={formatCurrency(view.realized_daily_savings)}
            />
            <ReadOnlyField
              label="Realizada / ano"
              hint={KAIZEN_HELP_TOOLTIPS.fields.realizedAnnual}
              value={formatCurrency(view.realized_annual_savings)}
            />
            <ReadOnlyField
              label="Efetividade"
              hint={KAIZEN_HELP_TOOLTIPS.fields.effectiveness}
              value={effectivenessLabel(view)}
            />
            <ReadOnlyField
              label="Contabiliza ganhos"
              hint={KAIZEN_HELP_TOOLTIPS.fields.savingsValidity}
              value={savingsAccountingLabel(view)}
              wide
            />
            <SavingsParamReadFields savingsType={view.savings_type} record={view} />
          </ReadOnlyGrid>
        }
        editContent={
          <FormGrid>
            <SelectField
              id="kz-d-savings-type"
              label="Tipo de economia"
              hint={KAIZEN_HELP_TOOLTIPS.fields.savingsType}
              value={form.savings_type}
              onChange={(value) =>
                updateField("savings_type", value as KaizenFormValues["savings_type"])
              }
              options={SAVINGS_TYPES}
              placeholderOption="Inferir automaticamente"
            />

            <SavingsParamFields
              savingsType={form.savings_type}
              values={form}
              onChange={(field, value) => updateField(field, value)}
              idPrefix="kz-d"
            />

            <TextField
              id="kz-d-realized"
              label="Economia realizada/dia (R$)"
              hint={KAIZEN_HELP_TOOLTIPS.fields.realizedDailySavings}
              inputMode="decimal"
              value={form.realized_daily_savings}
              onChange={(value) => updateField("realized_daily_savings", value)}
            />
            <TextField
              id="kz-d-eco-reason"
              label="Motivo da correção (registra na auditoria)"
              hint={KAIZEN_HELP_TOOLTIPS.fields.changeReason}
              span
              value={changeReason}
              onChange={setChangeReason}
            />
          </FormGrid>
        }
      />

      {/* Evidências da versão selecionada */}
      <SectionCard
        title={`Evidências da versão${selectedRevision != null ? ` v${selectedRevision}` : ""}`}
        hint={KAIZEN_HELP_TOOLTIPS.sections.evidences}
        subtitle={
          mode === "readonly"
            ? "Evidências desta versão histórica (somente leitura)."
            : `Registro visual Antes / Depois e anexos ${
                mode === "draft" ? "deste rascunho" : "da versão ativa"
              }. Cada versão tem suas próprias evidências.`
        }
      >
        <KaizenEvidencePanel
          kaizenId={record.id}
          readOnly={mode === "readonly"}
          revisionId={evidenceRevisionId}
        />
      </SectionCard>

      {/* Ganhos e validade */}
      <SectionCard
        title="Ganhos e validade"
        hint={KAIZEN_HELP_TOOLTIPS.improvements.periodGain}
        subtitle="Economia ativa hoje e ganho acumulado por período — só a versão implantada contabiliza, respeitando a validade de 1 ano."
      >
        <KaizenImprovementsPanel record={record} revisions={revisions} />
      </SectionCard>

      {/* Registro de alterações */}
      <SectionCard
        title="Registro de alterações"
        hint={KAIZEN_HELP_TOOLTIPS.sections.changelog}
        subtitle="Auditoria do kaizen como um todo: linha do tempo, versões e governança."
      >
        <KaizenChangeLog kaizenId={record.id} revisions={revisions} reloadKey={reloadTick} />
      </SectionCard>
    </>
  );
}
