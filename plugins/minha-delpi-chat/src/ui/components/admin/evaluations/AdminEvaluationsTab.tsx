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
      <header className="mdc-admin-evaluations__header">
        <div>
          <h2>Avaliação de respostas</h2>
          <p className="mdc-chat-muted">
            Avalie respostas do assistente, registre feedback e receba sugestões de melhoria para
            conhecimento e diretrizes.
          </p>
        </div>

        {summary ? (
          <div className="mdc-admin-evaluations__summary">
            <article>
              <span>Total</span>
              <strong>{summary.total}</strong>
            </article>
            <article>
              <span>Média</span>
              <strong>{summary.averageScore ?? "—"}</strong>
            </article>
            <article>
              <span>Úteis</span>
              <strong>
                {summary.helpfulRate !== null && summary.helpfulRate !== undefined
                  ? `${Math.round(summary.helpfulRate * 100)}%`
                  : "—"}
              </strong>
            </article>
            <article>
              <span>Hoje</span>
              <strong>{summary.recent24h}</strong>
            </article>
          </div>
        ) : null}
      </header>

      {error ? <p className="mdc-admin-evaluations__error">{error}</p> : null}
      {successMessage ? <p className="mdc-admin-evaluations__success">{successMessage}</p> : null}

      <div className="mdc-admin-evaluations__layout">
        <aside className="mdc-admin-evaluations__candidates">
          <label>
            <span>Buscar respostas</span>
            <input
              value={search}
              placeholder="Texto da resposta ou título da sessão"
              onChange={(event) => setSearch(event.target.value)}
            />
          </label>

          <button type="button" disabled={isLoading} onClick={() => void loadCandidates()}>
            {isLoading ? "Carregando..." : "Atualizar lista"}
          </button>

          <ul>
            {candidates.map((candidate) => (
              <li key={candidate.messageId}>
                <button
                  type="button"
                  className={
                    selectedMessageId === candidate.messageId
                      ? "is-selected"
                      : undefined
                  }
                  onClick={() => {
                    setSelectedMessageId(candidate.messageId);
                    setScore(candidate.evaluation?.score ?? 3);
                    setComment(candidate.evaluation?.comment ?? "");
                  }}
                >
                  <strong>{candidate.evaluation ? `★ ${candidate.evaluation.score}` : "Sem nota"}</strong>
                  <p>{candidate.contentPreview}</p>
                  <small>
                    {candidate.sourceCount} fonte(s) · {candidate.guidelineCount} diretriz(es)
                  </small>
                </button>
              </li>
            ))}
          </ul>
        </aside>

        <article className="mdc-admin-evaluations__detail">
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

              <label>
                <span>Comentário (opcional)</span>
                <textarea
                  value={comment}
                  rows={4}
                  placeholder="Descreva o que faltou ou o que funcionou bem."
                  onChange={(event) => setComment(event.target.value)}
                />
              </label>

              <label className="mdc-admin-evaluations__llm-toggle">
                <input
                  type="checkbox"
                  checked={useLlmSuggestions}
                  onChange={(event) => setUseLlmSuggestions(event.target.checked)}
                />
                <span>Enriquecer sugestões com LLM (mais lento)</span>
              </label>

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

              <button type="button" disabled={isSaving} onClick={() => void handleSave()}>
                {isSaving ? "Salvando..." : "Salvar avaliação"}
              </button>
            </>
          )}
        </article>
      </div>
    </section>
  );
}
