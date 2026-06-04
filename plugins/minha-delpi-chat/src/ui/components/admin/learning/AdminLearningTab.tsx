import { useCallback, useEffect, useMemo, useState } from "react";

import {
  approveAdminFineTuningDataset,
  createAdminFineTuningDataset,
  exportAdminFineTuningDataset,
  getAdminLearningSummary,
  createAdminEvaluationCase,
  listAdminEvaluationCases,
  listAdminFineTuningDatasets,
  listAdminFineTuningSamples,
  listAdminLearningCandidates,
  listAdminMemoryItems,
  listAdminVocabularyTerms,
  reviewAdminFineTuningSample,
  reviewAdminLearningCandidate,
  reviewAdminMemoryItem,
  runAdminEvaluationCases,
  upsertAdminVocabularyTerm,
} from "../../../../data/api/adminApi";
import type {
  AdminEvaluationCase,
  AdminFineTuningDataset,
  AdminFineTuningSample,
  AdminLearningCandidate,
  AdminLearningSummary,
  AdminMemoryItem,
  AdminVocabularyTerm,
} from "../../../../data/api/adminTypes";

import { LearningSummaryStrip } from "./LearningSummaryStrip";

import "./AdminLearningTab.css";

type AdminLearningTabProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

type LearningView =
  | "candidates"
  | "vocabulary"
  | "memory"
  | "evaluation"
  | "finetuning";

const FT_SAMPLE_STATUS_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "captured", label: "Capturadas" },
  { value: "approved", label: "Aprovadas" },
  { value: "rejected", label: "Rejeitadas" },
  { value: "", label: "Todas" },
];

const FT_SAMPLE_STATUS_LABELS: Record<string, string> = {
  captured: "Capturada",
  approved: "Aprovada",
  rejected: "Rejeitada",
};

const EVAL_STATUS_LABEL: Record<string, string> = {
  true: "Passou",
  false: "Falhou",
};

const MEMORY_STATUS_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "active", label: "Ativas" },
  { value: "forgotten", label: "Esquecidas" },
  { value: "", label: "Todas" },
];

const MEMORY_TYPE_LABELS: Record<string, string> = {
  preference: "Preferência",
  profile: "Perfil",
  correction: "Correção",
};

const STATUS_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "pending", label: "Pendentes" },
  { value: "approved", label: "Aprovados" },
  { value: "promoted", label: "Promovidos" },
  { value: "rejected", label: "Rejeitados" },
  { value: "", label: "Todos" },
];

const STATUS_LABELS: Record<string, string> = {
  pending: "Pendente",
  auto_approved: "Auto-aprovado",
  approved: "Aprovado",
  rejected: "Rejeitado",
  promoted: "Promovido",
  expired: "Expirado",
};

const TYPE_LABELS: Record<string, string> = {
  term_definition: "Definição de termo",
  normalization_rule: "Regra de normalização",
  vocabulary: "Vocabulário",
};

function formatConfidence(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "—";
  }
  return `${Math.round(value * 100)}%`;
}

export function AdminLearningTab({ getAccessToken }: AdminLearningTabProps) {
  const [view, setView] = useState<LearningView>("candidates");
  const [statusFilter, setStatusFilter] = useState<string>("pending");
  const [candidates, setCandidates] = useState<AdminLearningCandidate[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [terms, setTerms] = useState<AdminVocabularyTerm[]>([]);
  const [memoryItems, setMemoryItems] = useState<AdminMemoryItem[]>([]);
  const [memoryStatusFilter, setMemoryStatusFilter] = useState<string>("active");
  const [evalCases, setEvalCases] = useState<AdminEvaluationCase[]>([]);
  const [evalInput, setEvalInput] = useState("");
  const [evalIntent, setEvalIntent] = useState("assistant_identity");
  const [ftSamples, setFtSamples] = useState<AdminFineTuningSample[]>([]);
  const [ftDatasets, setFtDatasets] = useState<AdminFineTuningDataset[]>([]);
  const [ftSampleStatusFilter, setFtSampleStatusFilter] = useState<string>("captured");
  const [ftDatasetName, setFtDatasetName] = useState("");
  const [ftDatasetDescription, setFtDatasetDescription] = useState("");
  const [ftSelectedDatasetId, setFtSelectedDatasetId] = useState<number | null>(null);
  const [summary, setSummary] = useState<AdminLearningSummary | null>(null);
  const [isSummaryLoading, setIsSummaryLoading] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [isBusy, setIsBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Overrides usados na promoção.
  const [termOverride, setTermOverride] = useState("");
  const [normalizedOverride, setNormalizedOverride] = useState("");
  const [meaningOverride, setMeaningOverride] = useState("");

  // Form de novo termo de vocabulário.
  const [newTerm, setNewTerm] = useState("");
  const [newNormalized, setNewNormalized] = useState("");
  const [newMeaning, setNewMeaning] = useState("");
  const [newType, setNewType] = useState("typo");

  const selected = useMemo(
    () => candidates.find((item) => item.id === selectedId) ?? null,
    [candidates, selectedId],
  );

  const loadCandidates = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await listAdminLearningCandidates(
        { status: statusFilter || undefined, limit: 100 },
        { getAccessToken },
      );
      setCandidates(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar candidatos.");
    } finally {
      setIsLoading(false);
    }
  }, [getAccessToken, statusFilter]);

  const loadTerms = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await listAdminVocabularyTerms({ limit: 100 }, { getAccessToken });
      setTerms(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar vocabulário.");
    } finally {
      setIsLoading(false);
    }
  }, [getAccessToken]);

  const loadMemoryItems = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await listAdminMemoryItems(
        { status: memoryStatusFilter || undefined, limit: 100 },
        { getAccessToken },
      );
      setMemoryItems(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar memórias.");
    } finally {
      setIsLoading(false);
    }
  }, [getAccessToken, memoryStatusFilter]);

  const loadEvalCases = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await listAdminEvaluationCases({ limit: 100 }, { getAccessToken });
      setEvalCases(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar casos de teste.");
    } finally {
      setIsLoading(false);
    }
  }, [getAccessToken]);

  const loadFineTuning = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [samplesRes, datasetsRes] = await Promise.all([
        listAdminFineTuningSamples(
          { status: ftSampleStatusFilter || undefined, limit: 100 },
          { getAccessToken },
        ),
        listAdminFineTuningDatasets({ getAccessToken }),
      ]);
      setFtSamples(samplesRes.items);
      setFtDatasets(datasetsRes.items);
      setFtSelectedDatasetId(
        (prev) => prev ?? (datasetsRes.items[0]?.id != null ? datasetsRes.items[0].id : null),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar fine-tuning.");
    } finally {
      setIsLoading(false);
    }
  }, [ftSampleStatusFilter, getAccessToken]);

  const loadSummary = useCallback(async () => {
    setIsSummaryLoading(true);

    try {
      const response = await getAdminLearningSummary({ getAccessToken });
      setSummary(response);
    } catch {
      // KPIs são informativos; falha não deve bloquear a revisão.
      setSummary(null);
    } finally {
      setIsSummaryLoading(false);
    }
  }, [getAccessToken]);

  useEffect(() => {
    if (view === "candidates") {
      void loadCandidates();
    } else if (view === "vocabulary") {
      void loadTerms();
    } else if (view === "memory") {
      void loadMemoryItems();
    } else if (view === "evaluation") {
      void loadEvalCases();
    } else {
      void loadFineTuning();
    }
  }, [view, loadCandidates, loadTerms, loadMemoryItems, loadEvalCases, loadFineTuning]);

  useEffect(() => {
    void loadSummary();
  }, [loadSummary]);

  useEffect(() => {
    // Pré-preenche os overrides ao selecionar um candidato.
    setTermOverride(selected?.term ?? "");
    setNormalizedOverride(selected?.proposedRule ?? selected?.term ?? "");
    setMeaningOverride(selected?.proposedMeaning ?? "");
  }, [selected]);

  async function handleReview(action: "approve" | "reject" | "promote") {
    if (!selected) {
      return;
    }

    setIsBusy(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await reviewAdminLearningCandidate(
        selected.id,
        action === "promote"
          ? {
              action,
              term: termOverride.trim() || undefined,
              normalizedTerm: normalizedOverride.trim() || undefined,
              meaning: meaningOverride.trim() || undefined,
            }
          : { action },
        { getAccessToken },
      );

      setSuccessMessage(
        action === "promote"
          ? "Candidato promovido ao vocabulário aprovado."
          : action === "approve"
            ? "Candidato aprovado."
            : "Candidato rejeitado.",
      );
      setSelectedId(null);
      await loadCandidates();
      void loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao revisar candidato.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleRunEvaluations(caseId?: number) {
    setIsBusy(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const result = await runAdminEvaluationCases(
        caseId ? { caseId } : {},
        { getAccessToken },
      );
      const failed = Number(result.failed ?? 0);
      const passed = Number(result.passed ?? 0);

      setSuccessMessage(
        caseId
          ? "Caso executado."
          : `Execução concluída: ${passed} passou, ${failed} falhou.`,
      );
      await loadEvalCases();
      void loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao executar casos.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreateEvalCase() {
    if (!evalInput.trim()) {
      return;
    }

    setIsBusy(true);
    setError(null);

    try {
      await createAdminEvaluationCase(
        {
          category: "routing",
          input: evalInput.trim(),
          expectedIntent: evalIntent.trim() || undefined,
          mustNotUseTools: true,
          mustNotUseRag: true,
        },
        { getAccessToken },
      );
      setEvalInput("");
      setSuccessMessage("Caso de regressão criado.");
      await loadEvalCases();
      void loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar caso.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleMemoryReview(item: AdminMemoryItem, action: "forget" | "restore") {
    setIsBusy(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await reviewAdminMemoryItem(item.id, { action }, { getAccessToken });
      setSuccessMessage(
        action === "forget" ? "Memória esquecida." : "Memória restaurada.",
      );
      await loadMemoryItems();
      void loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao atualizar memória.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleReviewFtSample(sampleId: number, action: "approve" | "reject") {
    setIsBusy(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await reviewAdminFineTuningSample(
        sampleId,
        {
          action,
          datasetId:
            action === "approve" && ftSelectedDatasetId ? ftSelectedDatasetId : undefined,
        },
        { getAccessToken },
      );
      setSuccessMessage(action === "approve" ? "Amostra aprovada." : "Amostra rejeitada.");
      await loadFineTuning();
      void loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao revisar amostra.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreateFtDataset() {
    if (!ftDatasetName.trim()) {
      return;
    }

    setIsBusy(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const dataset = await createAdminFineTuningDataset(
        {
          name: ftDatasetName.trim(),
          description: ftDatasetDescription.trim() || undefined,
        },
        { getAccessToken },
      );
      setFtDatasetName("");
      setFtDatasetDescription("");
      setFtSelectedDatasetId(dataset.id);
      setSuccessMessage("Dataset criado.");
      await loadFineTuning();
      void loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar dataset.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleApproveFtDataset(datasetId: number) {
    setIsBusy(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await approveAdminFineTuningDataset(datasetId, { getAccessToken });
      setSuccessMessage("Dataset aprovado para exportação.");
      await loadFineTuning();
      void loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao aprovar dataset.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleExportFtDataset(datasetId: number) {
    setIsBusy(true);
    setError(null);

    try {
      const result = await exportAdminFineTuningDataset(datasetId, { getAccessToken });
      const blob = new Blob([result.jsonl], { type: "application/x-ndjson" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `fine-tuning-dataset-${datasetId}.jsonl`;
      anchor.click();
      URL.revokeObjectURL(url);
      setSuccessMessage("JSONL exportado.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao exportar dataset.");
    } finally {
      setIsBusy(false);
    }
  }

  async function handleCreateTerm() {
    if (!newTerm.trim()) {
      return;
    }

    setIsBusy(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await upsertAdminVocabularyTerm(
        {
          term: newTerm.trim(),
          normalizedTerm: newNormalized.trim() || undefined,
          meaning: newMeaning.trim() || undefined,
          type: newType,
          approved: true,
          active: true,
        },
        { getAccessToken },
      );

      setSuccessMessage("Termo salvo e aplicado à normalização.");
      setNewTerm("");
      setNewNormalized("");
      setNewMeaning("");
      await loadTerms();
      void loadSummary();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar termo.");
    } finally {
      setIsBusy(false);
    }
  }

  return (
    <section className="mdc-admin-learning">
      <header className="mdc-admin-learning__toolbar mdc-admin-tab-header">
        <div className="mdc-admin-page-header">
          <p className="mdc-chat-eyebrow">Conhecimento</p>
          <h2>Aprendizagem contínua</h2>
          <p>
            Revise candidatos de conhecimento aprendidos com o uso (typos, definições) e
            promova-os ao vocabulário aprovado, que passa a refinar a normalização do chat.
          </p>
        </div>

        <div className="mdc-admin-learning__views">
          <button
            type="button"
            className={view === "candidates" ? "is-active" : undefined}
            onClick={() => setView("candidates")}
          >
            Candidatos
          </button>
          <button
            type="button"
            className={view === "vocabulary" ? "is-active" : undefined}
            onClick={() => setView("vocabulary")}
          >
            Vocabulário
          </button>
          <button
            type="button"
            className={view === "memory" ? "is-active" : undefined}
            onClick={() => setView("memory")}
          >
            Memória
          </button>
          <button
            type="button"
            className={view === "evaluation" ? "is-active" : undefined}
            onClick={() => setView("evaluation")}
          >
            Regressão
          </button>
          <button
            type="button"
            className={view === "finetuning" ? "is-active" : undefined}
            onClick={() => setView("finetuning")}
          >
            Fine-tuning
          </button>
        </div>

        <button
          type="button"
          className="mdc-chat-ws-outline-btn"
          disabled={isLoading}
          onClick={() => {
            if (view === "candidates") {
              void loadCandidates();
            } else if (view === "vocabulary") {
              void loadTerms();
            } else if (view === "memory") {
              void loadMemoryItems();
            } else if (view === "evaluation") {
              void loadEvalCases();
            } else {
              void loadFineTuning();
            }
            void loadSummary();
          }}
        >
          {isLoading ? "Atualizando..." : "Atualizar"}
        </button>
      </header>

      <LearningSummaryStrip summary={summary} isLoading={isSummaryLoading} />

      {error ? <p className="mdc-admin-learning__error">{error}</p> : null}
      {successMessage ? (
        <p className="mdc-admin-learning__success">{successMessage}</p>
      ) : null}

      {view === "candidates" ? (
        <div className="mdc-admin-learning__layout mdc-admin-split">
          <aside className="mdc-admin-split__aside mdc-admin-panel">
            <label className="mdc-admin-field">
              <span>Status</span>
              <select
                value={statusFilter}
                onChange={(event) => {
                  setSelectedId(null);
                  setStatusFilter(event.target.value);
                }}
              >
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value || "all"} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <div className="mdc-admin-entity-list mdc-admin-learning__list">
              {candidates.length === 0 ? (
                <p className="mdc-chat-muted">Nenhum candidato neste filtro.</p>
              ) : null}

              {candidates.map((candidate) => (
                <button
                  key={candidate.id}
                  type="button"
                  className={[
                    "mdc-admin-learning__item",
                    selectedId === candidate.id ? "is-selected" : "",
                  ]
                    .filter(Boolean)
                    .join(" ")}
                  onClick={() => setSelectedId(candidate.id)}
                >
                  <div className="mdc-admin-entity-row__body">
                    <div className="mdc-admin-learning__item-head">
                      <strong>{candidate.term || candidate.inputText}</strong>
                      <span className={`mdc-admin-learning__badge is-${candidate.riskLevel}`}>
                        {formatConfidence(candidate.confidence)}
                      </span>
                    </div>
                    <p className="mdc-admin-entity-row__detail">
                      {TYPE_LABELS[candidate.candidateType] ?? candidate.candidateType}
                      {" · "}
                      {candidate.evidenceCount}× evidência
                    </p>
                    <small className="mdc-admin-entity-row__detail">
                      {STATUS_LABELS[candidate.status] ?? candidate.status} · {candidate.source}
                    </small>
                  </div>
                </button>
              ))}
            </div>
          </aside>

          <article className="mdc-admin-split__main mdc-admin-panel">
            {!selected ? (
              <p className="mdc-chat-muted">Selecione um candidato para revisar.</p>
            ) : (
              <div className="mdc-admin-learning__detail">
                <div className="mdc-admin-learning__field-readonly">
                  <span>Texto observado</span>
                  <p>{selected.inputText}</p>
                </div>

                <div className="mdc-admin-learning__meta-grid">
                  <div>
                    <span>Tipo</span>
                    <strong>
                      {TYPE_LABELS[selected.candidateType] ?? selected.candidateType}
                    </strong>
                  </div>
                  <div>
                    <span>Confiança</span>
                    <strong>{formatConfidence(selected.confidence)}</strong>
                  </div>
                  <div>
                    <span>Evidências</span>
                    <strong>{selected.evidenceCount}</strong>
                  </div>
                  <div>
                    <span>Escopo</span>
                    <strong>{selected.scope}</strong>
                  </div>
                </div>

                <label className="mdc-admin-field">
                  <span>Termo</span>
                  <input
                    value={termOverride}
                    onChange={(event) => setTermOverride(event.target.value)}
                    placeholder="forma que o chat deve reconhecer"
                  />
                </label>

                <label className="mdc-admin-field">
                  <span>Correção / forma normalizada</span>
                  <input
                    value={normalizedOverride}
                    onChange={(event) => setNormalizedOverride(event.target.value)}
                    placeholder="ex.: como voce se chama"
                  />
                </label>

                <label className="mdc-admin-field">
                  <span>Significado (opcional)</span>
                  <textarea
                    value={meaningOverride}
                    rows={3}
                    onChange={(event) => setMeaningOverride(event.target.value)}
                    placeholder="para definições de termo"
                  />
                </label>

                <div className="mdc-admin-learning__actions">
                  <button
                    type="button"
                    className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
                    disabled={isBusy}
                    onClick={() => void handleReview("promote")}
                  >
                    Promover ao vocabulário
                  </button>
                  <button
                    type="button"
                    className="mdc-chat-ws-outline-btn"
                    disabled={isBusy}
                    onClick={() => void handleReview("approve")}
                  >
                    Aprovar
                  </button>
                  <button
                    type="button"
                    className="mdc-admin-learning__danger"
                    disabled={isBusy}
                    onClick={() => void handleReview("reject")}
                  >
                    Rejeitar
                  </button>
                </div>
              </div>
            )}
          </article>
        </div>
      ) : view === "vocabulary" ? (
        <div className="mdc-admin-learning__layout mdc-admin-split">
          <aside className="mdc-admin-split__aside mdc-admin-panel">
            <h3 className="mdc-admin-learning__subtitle">Novo termo</h3>
            <label className="mdc-admin-field">
              <span>Termo (forma a reconhecer)</span>
              <input
                value={newTerm}
                onChange={(event) => setNewTerm(event.target.value)}
                placeholder="ex.: como vc s chama"
              />
            </label>
            <label className="mdc-admin-field">
              <span>Forma normalizada</span>
              <input
                value={newNormalized}
                onChange={(event) => setNewNormalized(event.target.value)}
                placeholder="ex.: como voce se chama"
              />
            </label>
            <label className="mdc-admin-field">
              <span>Tipo</span>
              <select value={newType} onChange={(event) => setNewType(event.target.value)}>
                <option value="typo">Typo</option>
                <option value="abbreviation">Abreviação</option>
                <option value="phrase">Expressão</option>
                <option value="term_definition">Definição de termo</option>
              </select>
            </label>
            <label className="mdc-admin-field">
              <span>Significado (opcional)</span>
              <textarea
                value={newMeaning}
                rows={2}
                onChange={(event) => setNewMeaning(event.target.value)}
              />
            </label>
            <button
              type="button"
              className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
              disabled={isBusy || !newTerm.trim()}
              onClick={() => void handleCreateTerm()}
            >
              Salvar termo
            </button>
          </aside>

          <article className="mdc-admin-split__main mdc-admin-panel">
            <h3 className="mdc-admin-learning__subtitle">Termos aprendidos</h3>
            <div className="mdc-admin-entity-list">
              {terms.length === 0 ? (
                <p className="mdc-chat-muted">Nenhum termo de vocabulário ainda.</p>
              ) : null}

              {terms.map((term) => (
                <div key={term.id} className="mdc-admin-learning__term">
                  <div className="mdc-admin-learning__item-head">
                    <strong>{term.term}</strong>
                    <span className="mdc-admin-learning__arrow">→ {term.normalizedTerm}</span>
                  </div>
                  <small className="mdc-admin-entity-row__detail">
                    {TYPE_LABELS[term.type] ?? term.type} · {term.scope}
                    {term.approved ? " · aprovado" : " · pendente"}
                    {term.active ? "" : " · inativo"}
                  </small>
                  {term.meaning ? (
                    <p className="mdc-admin-entity-row__detail">{term.meaning}</p>
                  ) : null}
                </div>
              ))}
            </div>
          </article>
        </div>
      ) : view === "memory" ? (
        <div className="mdc-admin-learning__layout">
          <div className="mdc-admin-panel">
            <div className="mdc-admin-learning__memory-toolbar">
              <label className="mdc-admin-field">
                <span>Status</span>
                <select
                  value={memoryStatusFilter}
                  onChange={(event) => setMemoryStatusFilter(event.target.value)}
                >
                  {MEMORY_STATUS_OPTIONS.map((option) => (
                    <option key={option.value || "all"} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
              <p className="mdc-chat-muted">
                Preferências e perfil duráveis aprendidos por usuário/projeto. Esquecer
                desativa o item imediatamente.
              </p>
            </div>

            <div className="mdc-admin-entity-list">
              {memoryItems.length === 0 ? (
                <p className="mdc-chat-muted">Nenhuma memória neste filtro.</p>
              ) : null}

              {memoryItems.map((item) => (
                <div key={item.id} className="mdc-admin-learning__memory-item">
                  <div className="mdc-admin-learning__memory-body">
                    <div className="mdc-admin-learning__item-head">
                      <strong>{item.content}</strong>
                      <span
                        className={`mdc-admin-learning__badge is-${
                          item.status === "active" ? "low" : "medium"
                        }`}
                      >
                        {item.status === "active" ? "Ativa" : "Esquecida"}
                      </span>
                    </div>
                    <small className="mdc-admin-entity-row__detail">
                      {MEMORY_TYPE_LABELS[item.type] ?? item.type} · {item.scope} ·{" "}
                      {item.evidenceCount}× · {item.source}
                    </small>
                  </div>

                  {item.status === "active" ? (
                    <button
                      type="button"
                      className="mdc-admin-learning__danger"
                      disabled={isBusy}
                      onClick={() => void handleMemoryReview(item, "forget")}
                    >
                      Esquecer
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="mdc-chat-ws-outline-btn"
                      disabled={isBusy}
                      onClick={() => void handleMemoryReview(item, "restore")}
                    >
                      Restaurar
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : view === "evaluation" ? (
        <div className="mdc-admin-learning__layout mdc-admin-split">
          <aside className="mdc-admin-split__aside mdc-admin-panel">
            <h3 className="mdc-admin-learning__subtitle">Novo caso</h3>
            <label className="mdc-admin-field">
              <span>Pergunta / entrada</span>
              <input
                value={evalInput}
                onChange={(event) => setEvalInput(event.target.value)}
                placeholder='ex.: "como vc s chama?"'
              />
            </label>
            <label className="mdc-admin-field">
              <span>Intenção esperada</span>
              <input
                value={evalIntent}
                onChange={(event) => setEvalIntent(event.target.value)}
                placeholder="assistant_identity"
              />
            </label>
            <button
              type="button"
              className="mdc-chat-ws-outline-btn"
              disabled={isBusy || !evalInput.trim()}
              onClick={() => void handleCreateEvalCase()}
            >
              Adicionar caso
            </button>
            <button
              type="button"
              className="mdc-chat-ws-primary-btn"
              disabled={isBusy}
              onClick={() => void handleRunEvaluations()}
            >
              Executar todos
            </button>
          </aside>

          <article className="mdc-admin-split__main mdc-admin-panel">
            <h3 className="mdc-admin-learning__subtitle">Casos de regressão</h3>
            <div className="mdc-admin-entity-list">
              {evalCases.length === 0 ? (
                <p className="mdc-chat-muted">Nenhum caso de regressão ainda.</p>
              ) : null}

              {evalCases.map((item) => (
                <div key={item.id} className="mdc-admin-learning__memory-item">
                  <div className="mdc-admin-learning__memory-body">
                    <div className="mdc-admin-learning__item-head">
                      <strong>{item.input}</strong>
                      <span
                        className={`mdc-admin-learning__badge is-${
                          item.lastPassed === false
                            ? "high"
                            : item.lastPassed === true
                              ? "low"
                              : "medium"
                        }`}
                      >
                        {item.lastPassed === null || item.lastPassed === undefined
                          ? "Não executado"
                          : EVAL_STATUS_LABEL[String(item.lastPassed)] ?? "—"}
                      </span>
                    </div>
                    <small className="mdc-admin-entity-row__detail">
                      {item.category}
                      {item.expectedIntent ? ` · ${item.expectedIntent}` : ""}
                      {item.status !== "active" ? ` · ${item.status}` : ""}
                    </small>
                    {item.lastFailureReason ? (
                      <p className="mdc-admin-learning__error">{item.lastFailureReason}</p>
                    ) : null}
                  </div>
                  <button
                    type="button"
                    className="mdc-chat-ws-outline-btn"
                    disabled={isBusy}
                    onClick={() => void handleRunEvaluations(item.id)}
                  >
                    Executar
                  </button>
                </div>
              ))}
            </div>
          </article>
        </div>
      ) : (
        <div className="mdc-admin-learning__layout mdc-admin-split">
          <aside className="mdc-admin-split__aside mdc-admin-panel">
            <h3 className="mdc-admin-learning__subtitle">Datasets</h3>
            <label className="mdc-admin-field">
              <span>Nome</span>
              <input
                value={ftDatasetName}
                onChange={(event) => setFtDatasetName(event.target.value)}
                placeholder="ex.: chat-v1-mar-2026"
              />
            </label>
            <label className="mdc-admin-field">
              <span>Descrição</span>
              <textarea
                value={ftDatasetDescription}
                rows={2}
                onChange={(event) => setFtDatasetDescription(event.target.value)}
              />
            </label>
            <button
              type="button"
              className="mdc-chat-ws-outline-btn"
              disabled={isBusy || !ftDatasetName.trim()}
              onClick={() => void handleCreateFtDataset()}
            >
              Criar dataset
            </button>

            <label className="mdc-admin-field">
              <span>Dataset para aprovar amostras</span>
              <select
                value={ftSelectedDatasetId ?? ""}
                onChange={(event) => {
                  const value = event.target.value;
                  setFtSelectedDatasetId(value ? Number(value) : null);
                }}
              >
                <option value="">— selecione —</option>
                {ftDatasets.map((dataset) => (
                  <option key={dataset.id} value={dataset.id}>
                    {dataset.name} ({dataset.status})
                  </option>
                ))}
              </select>
            </label>

            <label className="mdc-admin-field">
              <span>Status das amostras</span>
              <select
                value={ftSampleStatusFilter}
                onChange={(event) => setFtSampleStatusFilter(event.target.value)}
              >
                {FT_SAMPLE_STATUS_OPTIONS.map((option) => (
                  <option key={option.value || "all"} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </aside>

          <article className="mdc-admin-split__main mdc-admin-panel">
            <h3 className="mdc-admin-learning__subtitle">Datasets exportáveis</h3>
            <div className="mdc-admin-entity-list">
              {ftDatasets.length === 0 ? (
                <p className="mdc-chat-muted">Nenhum dataset ainda.</p>
              ) : null}

              {ftDatasets.map((dataset) => (
                <div key={dataset.id} className="mdc-admin-learning__memory-item">
                  <div className="mdc-admin-learning__memory-body">
                    <div className="mdc-admin-learning__item-head">
                      <strong>{dataset.name}</strong>
                      <span className="mdc-admin-learning__badge is-medium">
                        {dataset.status}
                      </span>
                    </div>
                    <small className="mdc-admin-entity-row__detail">
                      {dataset.targetModel}
                      {dataset.description ? ` · ${dataset.description}` : ""}
                    </small>
                  </div>
                  {dataset.status !== "approved" ? (
                    <button
                      type="button"
                      className="mdc-chat-ws-outline-btn"
                      disabled={isBusy}
                      onClick={() => void handleApproveFtDataset(dataset.id)}
                    >
                      Aprovar
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="mdc-chat-ws-primary-btn"
                      disabled={isBusy}
                      onClick={() => void handleExportFtDataset(dataset.id)}
                    >
                      Exportar JSONL
                    </button>
                  )}
                </div>
              ))}
            </div>

            <h3 className="mdc-admin-learning__subtitle">Amostras curadas</h3>
            <div className="mdc-admin-entity-list">
              {ftSamples.length === 0 ? (
                <p className="mdc-chat-muted">Nenhuma amostra neste filtro.</p>
              ) : null}

              {ftSamples.map((sample) => (
                <div key={sample.id} className="mdc-admin-learning__memory-item">
                  <div className="mdc-admin-learning__memory-body">
                    <div className="mdc-admin-learning__item-head">
                      <strong>
                        {sample.messages[0]?.content?.slice(0, 80) ?? `Amostra #${sample.id}`}
                      </strong>
                      <span
                        className={`mdc-admin-learning__badge is-${
                          sample.riskLevel === "high" ? "high" : "low"
                        }`}
                      >
                        {FT_SAMPLE_STATUS_LABELS[sample.status] ?? sample.status}
                      </span>
                    </div>
                    <small className="mdc-admin-entity-row__detail">
                      {sample.category} · {sample.source}
                      {sample.intentLabel ? ` · ${sample.intentLabel}` : ""}
                      {sample.anonymized ? " · anonimizada" : ""}
                    </small>
                  </div>
                  {sample.status === "captured" ? (
                    <div className="mdc-admin-learning__actions">
                      <button
                        type="button"
                        className="mdc-chat-ws-primary-btn"
                        disabled={isBusy || !ftSelectedDatasetId}
                        onClick={() => void handleReviewFtSample(sample.id, "approve")}
                      >
                        Aprovar
                      </button>
                      <button
                        type="button"
                        className="mdc-admin-learning__danger"
                        disabled={isBusy}
                        onClick={() => void handleReviewFtSample(sample.id, "reject")}
                      >
                        Rejeitar
                      </button>
                    </div>
                  ) : null}
                </div>
              ))}
            </div>
          </article>
        </div>
      )}
    </section>
  );
}
