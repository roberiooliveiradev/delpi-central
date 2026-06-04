import { useCallback, useEffect, useMemo, useState } from "react";

import {
  getAdminLearningSummary,
  listAdminLearningCandidates,
  listAdminVocabularyTerms,
  reviewAdminLearningCandidate,
  upsertAdminVocabularyTerm,
} from "../../../../data/api/adminApi";
import type {
  AdminLearningCandidate,
  AdminLearningSummary,
  AdminVocabularyTerm,
} from "../../../../data/api/adminTypes";

import { LearningSummaryStrip } from "./LearningSummaryStrip";

import "./AdminLearningTab.css";

type AdminLearningTabProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

type LearningView = "candidates" | "vocabulary";

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
    } else {
      void loadTerms();
    }
  }, [view, loadCandidates, loadTerms]);

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
        </div>

        <button
          type="button"
          className="mdc-chat-ws-outline-btn"
          disabled={isLoading}
          onClick={() => {
            void (view === "candidates" ? loadCandidates() : loadTerms());
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
      ) : (
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
      )}
    </section>
  );
}
