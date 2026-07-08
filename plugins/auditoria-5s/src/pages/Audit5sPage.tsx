import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowUp } from "lucide-react";

import {
  completeEvaluation,
  createArea,
  createAudit,
  deleteAudit,
  deleteResponseAttachment,
  fetchAreas,
  fetchAudit,
  fetchAudits,
  joinAudit,
  saveResponse,
  updateAudit,
  uploadResponseAttachment,
  type AuditDetail,
  type AuditListItem,
  type AuditArea,
  type AuditResponse,
  type Criterion,
} from "../api/audit5sApi";
import { getClientId } from "../utils/clientId";
import { AuditHeaderForm } from "../components/AuditHeaderForm";
import { AuditListView } from "../components/AuditListView";
import { AuditDashboardPage } from "./AuditDashboardPage";
import { AuditDetailHero } from "../components/AuditDetailHero";
import { AuditNcView } from "../components/AuditNcView";
import { CriterionPhotoSection } from "../components/CriterionPhotoSection";
import { ObservationTypingHint } from "../components/ObservationTypingHint";
import { AuditRealtimeBar } from "../components/AuditRealtimeBar";
import { AuditSensoScoreCards } from "../components/AuditSensoScoreCards";
import {
  CriterionScorePicker,
  getScoreSummaryLabel,
  getScoreTone,
} from "../components/CriterionScorePicker";
import {
  auditListSubtitle,
  branchFromPathname,
  canAccessNc,
  ncActionLabel,
  sensoName,
} from "../constants/audit5s";
import { useAudit5sRealtime } from "../hooks/useAudit5sRealtime";
import type { AuditAuditorSelection } from "../types/auditAuditor";
import type { AuditDashboardItem } from "../types/auditDashboard";
import { buildDefaultAuditors } from "../utils/auditAuditors";
import { formatPersonName } from "../utils/formatPersonName";
import { AuditPageHeader } from "../components/AuditPageHeader";

type Props = {
  pathname?: string;
};

type View = "list" | "new" | "edit" | "audit" | "nc" | "dashboard";

export function Audit5sPage({ pathname }: Props) {
  const branch = branchFromPathname(pathname);
  const [view, setView] = useState<View>("list");
  const [audits, setAudits] = useState<AuditListItem[]>([]);
  const [areas, setAreas] = useState<AuditArea[]>([]);
  const [selectedAudit, setSelectedAudit] = useState<AuditDetail | null>(null);
  const [activeSenso, setActiveSenso] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [newAreaName, setNewAreaName] = useState("");
  const [observationDrafts, setObservationDrafts] = useState<Record<string, string>>({});
  const [photoUploadingCriterionId, setPhotoUploadingCriterionId] = useState<string | null>(null);

  const [form, setForm] = useState({
    audit_date: new Date().toISOString().slice(0, 10),
    area_id: "",
    area_responsible: "",
    shift: "TURNO_1",
  });
  const [selectedAuditors, setSelectedAuditors] = useState<AuditAuditorSelection[]>(
    buildDefaultAuditors,
  );
  const [editingAuditId, setEditingAuditId] = useState<string | null>(null);

  const loadList = useCallback(async () => {
    if (!branch) return;
    setLoading(true);
    setError(null);
    try {
      const [auditItems, areaItems] = await Promise.all([
        fetchAudits(branch),
        fetchAreas(branch),
      ]);
      setAudits(auditItems);
      setAreas(areaItems);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dados.");
    } finally {
      setLoading(false);
    }
  }, [branch]);

  useEffect(() => {
    void loadList();
  }, [loadList]);

  const handleDeleteAudit = async (auditId: string) => {
    setError(null);
    setSuccess(null);
    try {
      await deleteAudit(auditId);
      if (selectedAudit?.id === auditId) {
        setSelectedAudit(null);
        setView("list");
      }
      await loadList();
      setSuccess("Auditoria excluída com sucesso.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir auditoria.");
    }
  };

  const openAudit = async (auditId: string) => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const detail = await joinAudit(auditId);
      setSelectedAudit(detail);
      setObservationDrafts({});
      setActiveSenso(1);
      setView("audit");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao abrir auditoria.");
    } finally {
      setLoading(false);
    }
  };

  const openNc = async (auditId: string) => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const detail = await joinAudit(auditId);
      if (!canAccessNc(detail.status)) {
        setError("Conclua a avaliação dos critérios antes de tratar as não conformidades.");
        return;
      }
      setSelectedAudit(detail);
      setView("nc");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao abrir não conformidades.");
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setSelectedAudit(null);
    setEditingAuditId(null);
    setError(null);
    setView("list");
  };

  const openNewAudit = () => {
    setEditingAuditId(null);
    setForm({
      audit_date: new Date().toISOString().slice(0, 10),
      area_id: "",
      area_responsible: "",
      shift: "TURNO_1",
    });
    setSelectedAuditors(buildDefaultAuditors());
    setNewAreaName("");
    setError(null);
    setSuccess(null);
    setView("new");
  };

  const handleCreateArea = async () => {
    if (!branch || !newAreaName.trim()) return;
    try {
      const area = await createArea(branch, newAreaName.trim());
      setAreas((prev) => [...prev, area].sort((a, b) => a.name.localeCompare(b.name)));
      setForm((prev) => ({ ...prev, area_id: area.id }));
      setNewAreaName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao cadastrar área.");
    }
  };

  const buildAuditorsPayload = () =>
    selectedAuditors.map((auditor) => ({
      user_id: auditor.user_id,
      display_name: formatPersonName(auditor.display_name) || auditor.display_name,
    }));

  const openEditAudit = async (auditId: string) => {
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      const detail = await fetchAudit(auditId);
      if (detail.status === "closed") {
        setError("Auditoria encerrada — o cabeçalho não pode mais ser editado.");
        return;
      }
      setEditingAuditId(detail.id);
      setForm({
        audit_date: detail.audit_date.slice(0, 10),
        area_id: detail.area_id,
        area_responsible: detail.area_responsible,
        shift: detail.shift,
      });
      setSelectedAuditors(
        detail.auditors.map((auditor) => ({
          user_id: auditor.user_id,
          display_name: auditor.display_name,
        })),
      );
      setNewAreaName("");
      setView("edit");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar auditoria.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateAudit = async () => {
    if (!branch) return;
    setLoading(true);
    setError(null);
    try {
      const audit = await createAudit({
        branch_code: branch,
        audit_date: form.audit_date,
        area_id: form.area_id,
        area_responsible: formatPersonName(form.area_responsible.trim()) || form.area_responsible.trim(),
        shift: form.shift,
        auditors: buildAuditorsPayload(),
      });
      setSelectedAudit(audit);
      setObservationDrafts({});
      setActiveSenso(1);
      setView("audit");
      await loadList();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar auditoria.");
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateAudit = async () => {
    if (!editingAuditId) return;
    setLoading(true);
    setError(null);
    setSuccess(null);
    try {
      await updateAudit(editingAuditId, {
        audit_date: form.audit_date,
        area_id: form.area_id,
        area_responsible: formatPersonName(form.area_responsible.trim()) || form.area_responsible.trim(),
        shift: form.shift,
        auditors: buildAuditorsPayload(),
      });
      setEditingAuditId(null);
      await loadList();
      setView("list");
      setSuccess("Cabeçalho da auditoria atualizado com sucesso.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao atualizar cabeçalho.");
    } finally {
      setLoading(false);
    }
  };

  const criteriaBySenso = useMemo(() => {
    const map = new Map<number, Criterion[]>();
    if (!selectedAudit) return map;
    for (const criterion of selectedAudit.criteria) {
      const list = map.get(criterion.senso_order) ?? [];
      list.push(criterion);
      map.set(criterion.senso_order, list);
    }
    return map;
  }, [selectedAudit]);

  const sensoNamesByOrder = useMemo(() => {
    const map = new Map<number, string>();
    selectedAudit?.criteria.forEach((criterion) => {
      if (!map.has(criterion.senso_order)) {
        map.set(criterion.senso_order, criterion.senso_name);
      }
    });
    return map;
  }, [selectedAudit]);

  const activeSensoName = sensoName(activeSenso, sensoNamesByOrder.get(activeSenso), branch);

  const resyncSelectedAudit = useCallback(async () => {
    if (!selectedAudit) return;
    try {
      const detail = await fetchAudit(selectedAudit.id);
      setSelectedAudit(detail);
    } catch {
      // falha silenciosa no resync em background
    }
  }, [selectedAudit]);

  const realtimeEnabled = Boolean(
    selectedAudit && (view === "audit" || view === "nc"),
  );

  const { connected, connectionError, presence, observationTyping, notice, dismissNotice, signalObservationTyping, stopObservationTyping } =
    useAudit5sRealtime({
    auditId: selectedAudit?.id ?? null,
    enabled: realtimeEnabled,
    onAuditSync: setSelectedAudit,
    onResync: () => {
      void resyncSelectedAudit();
    },
  });

  const selfClientId = getClientId();

  const responseMap = useMemo(() => {
    const map = new Map<string, AuditResponse>();
    selectedAudit?.responses.forEach((item) => map.set(item.criterion_id, item));
    return map;
  }, [selectedAudit]);

  const getObservationValue = (criterionId: string, response?: AuditResponse) =>
    observationDrafts[criterionId] ?? response?.observation ?? "";

  const normalizeObservation = (value: string) => {
    const trimmed = value.trim();
    return trimmed.length > 0 ? trimmed : null;
  };

  const handleScore = async (
    criterionId: string,
    payload: { score: number | null; is_not_applicable: boolean },
  ) => {
    if (!selectedAudit) return;
    setError(null);
    try {
      const existing = responseMap.get(criterionId);
      const result = await saveResponse(selectedAudit.id, criterionId, {
        ...payload,
        observation: normalizeObservation(getObservationValue(criterionId, existing)),
        version: existing?.version ?? null,
      });
      setSelectedAudit(result.audit);
      setObservationDrafts((prev) => {
        const next = { ...prev };
        delete next[criterionId];
        return next;
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao salvar nota.";
      if (message.toLowerCase().includes("conflito")) {
        await resyncSelectedAudit();
        setError("Outro auditor alterou este critério. Dados atualizados — confira a nota e tente novamente.");
        return;
      }
      setError(message);
    }
  };

  const handleObservationBlur = async (criterionId: string) => {
    stopObservationTyping(criterionId);

    if (!selectedAudit || selectedAudit.status !== "draft") return;

    const existing = responseMap.get(criterionId);
    if (!existing || (existing.score == null && !existing.is_not_applicable)) {
      return;
    }

    const nextObservation = normalizeObservation(getObservationValue(criterionId, existing));
    const currentObservation = normalizeObservation(existing.observation ?? "");
    if (nextObservation === currentObservation) {
      return;
    }

    setError(null);
    try {
      const result = await saveResponse(selectedAudit.id, criterionId, {
        score: existing.is_not_applicable ? null : existing.score,
        is_not_applicable: existing.is_not_applicable,
        observation: nextObservation,
        version: existing.version ?? null,
      });
      setSelectedAudit(result.audit);
      setObservationDrafts((prev) => {
        const next = { ...prev };
        delete next[criterionId];
        return next;
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar observação.");
    }
  };

  const handleComplete = async () => {
    if (!selectedAudit) return;
    setError(null);
    setSuccess(null);
    try {
      const audit = await completeEvaluation(selectedAudit.id);
      await loadList();
      setSelectedAudit(null);
      setView("list");
      setSuccess(
        `Avaliação ${audit.audit_code} concluída. Use o botão "${ncActionLabel(audit.status)}" na lista para tratar as não conformidades.`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao concluir avaliação.");
    }
  };

  const patchResponseAttachment = (
    criterionId: string,
    attachment: AuditResponse["attachment"] | null,
  ) => {
    setSelectedAudit((prev) => {
      if (!prev) return prev;
      return {
        ...prev,
        responses: prev.responses.map((item) =>
          item.criterion_id === criterionId ? { ...item, attachment } : item,
        ),
      };
    });
  };

  const handleCriterionPhotoUpload = async (criterionId: string, file: File) => {
    if (!selectedAudit) return;
    setError(null);
    setPhotoUploadingCriterionId(criterionId);
    try {
      const attachment = await uploadResponseAttachment(selectedAudit.id, criterionId, file);
      patchResponseAttachment(criterionId, attachment);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao anexar foto.";
      setError(message);
      throw err instanceof Error ? err : new Error(message);
    } finally {
      setPhotoUploadingCriterionId(null);
    }
  };

  const handleCriterionPhotoRemove = async (criterionId: string, attachmentId: string) => {
    if (!selectedAudit) return;
    setError(null);
    try {
      await deleteResponseAttachment(selectedAudit.id, criterionId, attachmentId);
      patchResponseAttachment(criterionId, null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erro ao remover foto.";
      setError(message);
      throw err instanceof Error ? err : new Error(message);
    }
  };

  if (!branch) {
    return (
      <div className="dashboard-auditoria-5s dashboard-page a5s-app">
        <div className="a5s-app-shell">
          <div className="a5s-alert a5s-alert--error" role="alert">
            Rota inválida. Use /apps/auditoria-5s/filial-01 ou filial-02.
          </div>
        </div>
      </div>
    );
  }

  const handleDashboardItem = (item: AuditDashboardItem) => {
    if (canAccessNc(item.status)) {
      void openNc(item.id);
      return;
    }
    void openAudit(item.id);
  };

  const pageSubtitle =
    view === "new"
      ? "Preencha os dados para iniciar uma nova avaliação."
      : view === "edit"
        ? "Atualize data, área, responsável, turno e auditores desta auditoria."
        : view === "audit"
        ? "Avalie os critérios por senso e acompanhe o progresso em tempo real."
        : view === "nc"
          ? "Registre ações corretivas para os critérios com nota baixa desta auditoria."
          : view === "dashboard"
            ? "Acompanhe a evolução das auditorias com filtros e gráficos gerenciais."
            : auditListSubtitle(branch);

  return (
    <div
      className={`dashboard-auditoria-5s dashboard-page a5s-app ${view === "list" ? "a5s-app--dashboard" : ""} ${view === "nc" ? "a5s-app--nc" : ""} ${view === "dashboard" ? "a5s-app--analytics" : ""}`}
    >
      <div className="a5s-app-shell">
      {view !== "list" ? (
        <AuditPageHeader
          branch={branch}
          title={
            view === "nc"
              ? "Tratar não conformidades"
              : view === "dashboard"
                ? "Dashboard gerencial"
                : undefined
          }
          subtitle={pageSubtitle}
          showBack
          onBack={handleBack}
        />
      ) : null}

      {error && <div className="a5s-alert a5s-alert--error">{error}</div>}
      {success && <div className="a5s-alert a5s-alert--success">{success}</div>}

      {view === "list" && (
        <AuditListView
          branch={branch}
          audits={audits}
          areas={areas}
          loading={loading}
          onNew={openNewAudit}
          onOpenDashboard={() => setView("dashboard")}
          onOpenAudit={(auditId) => void openAudit(auditId)}
          onOpenNc={(auditId) => void openNc(auditId)}
          onEditAudit={(auditId) => void openEditAudit(auditId)}
          onDeleteAudit={handleDeleteAudit}
        />
      )}

      {view === "dashboard" && (
        <AuditDashboardPage
          branch={branch}
          areas={areas}
          audits={audits}
          onOpenItem={handleDashboardItem}
        />
      )}

      {view === "new" && (
        <AuditHeaderForm
          title="Nova auditoria"
          areas={areas}
          form={form}
          onFormChange={(patch) => setForm((prev) => ({ ...prev, ...patch }))}
          selectedAuditors={selectedAuditors}
          onAuditorsChange={setSelectedAuditors}
          newAreaName={newAreaName}
          onNewAreaNameChange={setNewAreaName}
          onCreateArea={handleCreateArea}
          submitLabel="Iniciar auditoria"
          loading={loading}
          onSubmit={handleCreateAudit}
        />
      )}

      {view === "edit" && (
        <AuditHeaderForm
          title="Editar cabeçalho"
          areas={areas}
          form={form}
          onFormChange={(patch) => setForm((prev) => ({ ...prev, ...patch }))}
          selectedAuditors={selectedAuditors}
          onAuditorsChange={setSelectedAuditors}
          newAreaName={newAreaName}
          onNewAreaNameChange={setNewAreaName}
          onCreateArea={handleCreateArea}
          submitLabel="Salvar alterações"
          loading={loading}
          onSubmit={handleUpdateAudit}
        />
      )}

      {view === "audit" && selectedAudit && (
        <section className="a5s-panel">
          <AuditRealtimeBar
            connected={connected}
            connectionError={connectionError}
            presence={presence}
            notice={notice}
            onDismissNotice={dismissNotice}
          />
          <AuditDetailHero audit={selectedAudit} />

          <AuditSensoScoreCards
            audit={selectedAudit}
            sensoNamesByOrder={sensoNamesByOrder}
            activeSenso={activeSenso}
            onSelectSenso={setActiveSenso}
          />

          <h2 className="a5s-senso-heading">
            Senso {activeSenso} — {activeSensoName}
          </h2>

          <div className="a5s-criteria-list">
            {(criteriaBySenso.get(activeSenso) ?? []).map((criterion: Criterion) => {
              const response = responseMap.get(criterion.id);
              const disabled = selectedAudit.status !== "draft";
              const hasScore = Boolean(
                response && (response.is_not_applicable || response.score != null),
              );
              const observationValue = getObservationValue(criterion.id, response);
              const scoreTone = getScoreTone(response?.score, Boolean(response?.is_not_applicable));
              const scoreSummary = getScoreSummaryLabel(
                response?.score,
                Boolean(response?.is_not_applicable),
              );
              const showCriterionPhoto =
                Boolean(response) &&
                !response?.is_not_applicable &&
                (response?.score === 1 || response?.score === 3);
              return (
                <article
                  key={criterion.id}
                  className={`a5s-criterion ${scoreTone ? `a5s-criterion--${scoreTone}` : ""}`}
                >
                  <div className="a5s-criterion__head">
                    <div className="a5s-criterion__title-row">
                      <span className="a5s-criterion__code">{criterion.code}</span>
                      {scoreSummary && scoreTone ? (
                        <span className={`a5s-criterion__badge a5s-criterion__badge--${scoreTone}`}>
                          {scoreSummary}
                        </span>
                      ) : null}
                    </div>
                    <p>{criterion.description}</p>
                  </div>
                  <CriterionScorePicker
                    disabled={disabled}
                    score={response?.score}
                    isNotApplicable={Boolean(response?.is_not_applicable)}
                    onSelect={(payload) => void handleScore(criterion.id, payload)}
                  />
                  <div className="a5s-criterion__observation">
                    <label htmlFor={`obs-${criterion.id}`}>Observação (opcional)</label>
                    <ObservationTypingHint
                      users={observationTyping[criterion.id] ?? []}
                      selfClientId={selfClientId}
                    />
                    <textarea
                      id={`obs-${criterion.id}`}
                      rows={2}
                      placeholder={
                        hasScore
                          ? "Comentário sobre este critério..."
                          : "Informe a nota antes de adicionar observação."
                      }
                      value={observationValue}
                      disabled={disabled || !hasScore}
                      onFocus={() => {
                        if (!disabled && hasScore) {
                          signalObservationTyping(criterion.id);
                        }
                      }}
                      onChange={(e) => {
                        setObservationDrafts((prev) => ({
                          ...prev,
                          [criterion.id]: e.target.value,
                        }));
                        if (!disabled && hasScore) {
                          signalObservationTyping(criterion.id);
                        }
                      }}
                      onBlur={() => void handleObservationBlur(criterion.id)}
                    />
                  </div>
                  {showCriterionPhoto ? (
                    <CriterionPhotoSection
                      auditId={selectedAudit.id}
                      criterionId={criterion.id}
                      attachment={response?.attachment}
                      disabled={disabled}
                      uploading={photoUploadingCriterionId === criterion.id}
                      onUpload={(file) => handleCriterionPhotoUpload(criterion.id, file)}
                      onRemove={async () => {
                        if (!response?.attachment) return;
                        await handleCriterionPhotoRemove(criterion.id, response.attachment.id);
                      }}
                    />
                  ) : null}
                </article>
              );
            })}
          </div>

          {selectedAudit.status === "draft" && (
            <div className="a5s-panel__actions">
              <button
                type="button"
                className="a5s-btn"
                disabled={selectedAudit.progress.pending > 0}
                onClick={() => void handleComplete()}
              >
                Concluir avaliação
              </button>
              {selectedAudit.progress.pending > 0 && (
                <span className="a5s-hint">
                  Todos os critérios precisam de nota (1, 3, 5 ou NA).
                </span>
              )}
            </div>
          )}

          {selectedAudit.status !== "draft" && (
            <div className="a5s-audit-complete-hint">
              <p>Avaliação concluída. Volte à lista e acesse <strong>Tratar NC</strong> para registrar não conformidades.</p>
            </div>
          )}

          <footer className="a5s-audit-footer">
            <button
              type="button"
              className="a5s-btn a5s-btn--ghost a5s-audit-footer__top"
              onClick={() => {
                document.getElementById("a5s-senso-nav")?.scrollIntoView({
                  behavior: "smooth",
                  block: "start",
                });
              }}
            >
              <ArrowUp size={16} aria-hidden />
              Voltar aos sensos
            </button>
          </footer>
        </section>
      )}

      {view === "nc" && selectedAudit && (
        <>
          <AuditRealtimeBar
            connected={connected}
            connectionError={connectionError}
            presence={presence}
            notice={notice}
            onDismissNotice={dismissNotice}
          />
          <AuditNcView
            audit={selectedAudit}
            onAuditUpdated={setSelectedAudit}
            onClosed={() => {
              void loadList();
              handleBack();
            }}
          />
        </>
      )}
      </div>
    </div>
  );
}
