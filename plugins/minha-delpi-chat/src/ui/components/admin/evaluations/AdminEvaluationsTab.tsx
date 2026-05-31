import { useCallback, useEffect, useState } from "react";

import {
  getAdminResponseEvaluationContext,
  getAdminResponseEvaluationSummary,
  listAdminResponseCandidates,
  saveAdminResponseEvaluation,
} from "../../../../data/api/adminApi";
import type {
  AdminResponseEvaluationContext,
  AdminResponseEvaluationSummary,
  AdminResponseCandidate,
} from "../../../../data/api/adminTypes";

import { AdminFormCheckbox } from "../shared/AdminFormCheckbox";
import { EvaluationsSummaryStrip } from "./EvaluationsSummaryStrip";

import "./AdminEvaluationsTab.css";

type AdminEvaluationsTabProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

const SCORE_OPTIONS = [1, 2, 3, 4, 5];

export function AdminEvaluationsTab({ getAccessToken }: AdminEvaluationsTabProps) {
  const [summary, setSummary] = useState<AdminResponseEvaluationSummary | null>(null);
  const [candidates, setCandidates] = useState<AdminResponseCandidate[]>([]);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const [context, setContext] = useState<AdminResponseEvaluationContext | null>(null);
  const [score, setScore] = useState(3);
  const [comment, setComment] = useState("");
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [useLlmSuggestions, setUseLlmSuggestions] = useState(false);

  const loadCandidates = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const [summaryResponse, candidatesResponse] = await Promise.all([
        getAdminResponseEvaluationSummary({ getAccessToken }),
        listAdminResponseCandidates({ search: search || undefined, limit: 30 }, { getAccessToken }),
      ]);

      setSummary(summaryResponse);
      setCandidates(candidatesResponse.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar avaliações.");
    } finally {
      setIsLoading(false);
    }
  }, [getAccessToken, search]);

  const loadContext = useCallback(
    async (messageId: string, nextScore: number) => {
      try {
        const response = await getAdminResponseEvaluationContext(messageId, nextScore, {
          getAccessToken,
          useLlmSuggestions,
        });
        setContext(response);
        setScore(response.evaluation?.score ?? nextScore);
        setComment(response.evaluation?.comment ?? "");
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao carregar contexto da resposta.");
      }
    },
    [getAccessToken, useLlmSuggestions],
  );

  useEffect(() => {
    void loadCandidates();
  }, [loadCandidates]);

  useEffect(() => {
    if (!selectedMessageId) {
      setContext(null);
      return;
    }

    void loadContext(selectedMessageId, score);
  }, [loadContext, score, selectedMessageId]);

  async function handleSave() {
    if (!selectedMessageId) {
      return;
    }

    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await saveAdminResponseEvaluation(
        {
          messageId: selectedMessageId,
          score,
          comment: comment.trim() || undefined,
        },
        { getAccessToken },
      );

      setSuccessMessage("Avaliação salva com sugestões registradas.");
      await loadCandidates();

      if (selectedMessageId) {
        await loadContext(selectedMessageId, score);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao salvar avaliação.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="mdc-admin-evaluations">
      <header className="mdc-admin-evaluations__toolbar mdc-admin-tab-header">
        <div className="mdc-admin-page-header">
          <p className="mdc-chat-eyebrow">Qualidade</p>
          <h2>Avaliação de respostas</h2>
          <p>
            Avalie respostas do assistente, registre feedback e receba sugestões de melhoria para
            conhecimento e diretrizes.
          </p>
        </div>

        <EvaluationsSummaryStrip summary={summary} isLoading={isLoading} />

        <button
          type="button"
          className="mdc-chat-ws-outline-btn"
          disabled={isLoading}
          onClick={() => void loadCandidates()}
        >
          {isLoading ? "Atualizando..." : "Atualizar"}
        </button>
      </header>

      {error ? <p className="mdc-admin-evaluations__error">{error}</p> : null}
      {successMessage ? <p className="mdc-admin-evaluations__success">{successMessage}</p> : null}

      <div className="mdc-admin-evaluations__layout mdc-admin-split">
        <aside className="mdc-admin-split__aside mdc-admin-panel mdc-admin-evaluations__candidates">
          <label className="mdc-admin-field">
            <span>Buscar respostas</span>
            <input
              value={search}
              placeholder="Texto da resposta ou título da sessão"
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>

          <div className="mdc-admin-entity-list mdc-admin-evaluations__candidate-list">
            {candidates.map((candidate) => (
              <button
                key={candidate.messageId}
                type="button"
                className={[
                  "mdc-admin-evaluations__candidate",
                  selectedMessageId === candidate.messageId ? "is-selected" : "",
                ]
                  .filter(Boolean)
                  .join(" ")}
                onClick={() => {
                  setSelectedMessageId(candidate.messageId);
                  setScore(candidate.evaluation?.score ?? 3);
                  setComment(candidate.evaluation?.comment ?? "");
                }}
              >
                <div className="mdc-admin-entity-row__body">
                  <div className="mdc-admin-entity-row__title-line">
                    <strong>
                      {candidate.evaluation
                        ? `★ ${candidate.evaluation.score}`
                        : "Sem nota"}
                    </strong>
                  </div>
                  <p className="mdc-admin-entity-row__detail">{candidate.contentPreview}</p>
                  <small className="mdc-admin-entity-row__detail">
                    {candidate.sourceCount} fonte(s) · {candidate.guidelineCount} diretriz(es)
                  </small>
                </div>
              </button>
            ))}
          </div>
        </aside>

        <article className="mdc-admin-split__main mdc-admin-panel mdc-admin-evaluations__detail">
          {!selectedMessageId || !context ? (
            <p className="mdc-chat-muted">Selecione uma resposta do assistente para avaliar.</p>
          ) : (
            <>
              <div className="mdc-admin-evaluations__question">
                <span>Pergunta do usuário</span>
                <p>{context.userQuestion || "—"}</p>
              </div>

              <div className="mdc-admin-evaluations__answer">
                <span>Resposta do assistente</span>
                <p>{context.message.content}</p>
              </div>

              <div className="mdc-admin-evaluations__score">
                <span>Nota (1-5)</span>
                <div>
                  {SCORE_OPTIONS.map((value) => (
                    <button
                      key={value}
                      type="button"
                      className={score === value ? "is-active" : undefined}
                      onClick={() => setScore(value)}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              </div>

              <label className="mdc-admin-field">
                <span>Comentário (opcional)</span>
                <textarea
                  value={comment}
                  rows={4}
                  placeholder="Descreva o que faltou ou o que funcionou bem."
                  onChange={(event) => setComment(event.target.value)}
                />
              </label>

              <AdminFormCheckbox
                title="Enriquecer sugestões com LLM"
                hint="Mais lento; gera sugestões adicionais com base no contexto da resposta."
                checked={useLlmSuggestions}
                onChange={(event) => setUseLlmSuggestions(event.target.checked)}
              />

              <div className="mdc-admin-evaluations__suggestions">
                <h3>Sugestões automáticas</h3>

                {(context.suggestions.documents ?? []).length === 0 &&
                (context.suggestions.guidelines ?? []).length === 0 ? (
                  <p className="mdc-chat-muted">Nenhuma sugestão adicional para este cenário.</p>
                ) : null}

                {(context.suggestions.documents ?? []).map((item, index) => (
                  <article key={`doc-${index}`}>
                    <strong>Conhecimento · {item.type}</strong>
                    <p>{item.reason}</p>
                    <small>{item.suggestedAction}</small>
                  </article>
                ))}

                {(context.suggestions.guidelines ?? []).map((item, index) => (
                  <article key={`guide-${index}`}>
                    <strong>Diretriz · {item.type}</strong>
                    <p>{item.reason}</p>
                    <small>{item.suggestedAction}</small>
                  </article>
                ))}
              </div>

              <button
                type="button"
                className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
                disabled={isSaving}
                onClick={() => void handleSave()}
              >
                {isSaving ? "Salvando..." : "Salvar avaliação"}
              </button>
            </>
          )}
        </article>
      </div>
    </section>
  );
}
