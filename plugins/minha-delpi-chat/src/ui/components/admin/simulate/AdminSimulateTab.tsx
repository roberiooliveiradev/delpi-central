import { useEffect, useMemo, useState } from "react";

import { listChatAgents, listChatSessions } from "../../../../data/api/chatApi";
import type { ChatSession } from "../../../../data/api/chatTypes";
import type { ChatAgent } from "../../../../data/api/chatTypes";
import { simulateAdminAgent } from "../../../../data/api/adminApi";
import type { AdminAgentSimulateResponse } from "../../../../data/api/adminTypes";

import { SimulateSummaryStrip } from "./SimulateSummaryStrip";
import { computeSimulateSummary } from "./simulateSummary";

import "./AdminSimulateTab.css";

type AdminSimulateTabProps = {
  getAccessToken?: () => string | undefined | Promise<string | undefined>;
};

export function AdminSimulateTab({ getAccessToken }: AdminSimulateTabProps) {
  const [question, setQuestion] = useState("");
  const [agentId, setAgentId] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [executeToolsInSandbox, setExecuteToolsInSandbox] = useState(false);
  const [generateAnswer, setGenerateAnswer] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [agents, setAgents] = useState<ChatAgent[]>([]);
  const [result, setResult] = useState<AdminAgentSimulateResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAgents() {
      try {
        const [agentsResponse, sessionsResponse] = await Promise.all([
          listChatAgents({ getAccessToken }),
          listChatSessions({ getAccessToken }),
        ]);
        setAgents(agentsResponse);
        setSessions(sessionsResponse);
      } catch {
        setAgents([]);
        setSessions([]);
      }
    }

    void loadAgents();
  }, [getAccessToken]);

  const summary = useMemo(
    () => computeSimulateSummary(agents.length, sessions.length, Boolean(result)),
    [agents.length, sessions.length, result],
  );

  function handleClear() {
    setQuestion("");
    setResult(null);
    setError(null);
  }

  async function handleSimulate() {
    const normalized = question.trim();

    if (!normalized || isLoading) {
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await simulateAdminAgent(
        {
          question: normalized,
          agentId: agentId || undefined,
          sessionId: sessionId || undefined,
          executeToolsInSandbox,
          generateAnswer,
        },
        { getAccessToken },
      );
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao simular agente.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <section className="mdc-admin-simulate">
      <header className="mdc-admin-simulate__toolbar mdc-admin-tab-header">
        <div className="mdc-admin-page-header">
          <p className="mdc-chat-eyebrow">Simulação</p>
          <h2>Simulação completa do agente</h2>
          <p>
            Valide prompt final, diretrizes, RAG e tools previstas antes de publicar alterações.
          </p>
        </div>

        <SimulateSummaryStrip summary={summary} />

        <div className="mdc-admin-simulate__toolbar-actions">
          <button
            type="button"
            className="mdc-chat-ws-outline-btn"
            disabled={!result && !error && !question.trim()}
            onClick={handleClear}
          >
            Limpar
          </button>
        </div>
      </header>

      <div className="mdc-admin-simulate__layout mdc-admin-split">
        <div className="mdc-admin-split__aside">
          <article className="mdc-admin-panel mdc-admin-simulate__form">
        <label className="mdc-admin-field">
          <span>Pergunta de teste</span>
          <textarea
            value={question}
            rows={4}
            placeholder="Ex.: Como devo responder sobre férias?"
            onChange={(event) => setQuestion(event.target.value)}
          />
        </label>

        <label className="mdc-admin-field">
          <span>Agente (opcional)</span>
          <select value={agentId} onChange={(event) => setAgentId(event.target.value)}>
            <option value="">Padrão do chat</option>
            {agents.map((agent) => (
              <option key={agent.id} value={agent.id}>
                {agent.name}
              </option>
            ))}
          </select>
        </label>

        <label className="mdc-admin-field">
          <span>Sessão real (opcional)</span>
          <select value={sessionId} onChange={(event) => setSessionId(event.target.value)}>
            <option value="">Sem histórico de sessão</option>
            {sessions.map((session) => (
              <option key={session.id} value={session.id}>
                {session.title || session.id}
              </option>
            ))}
          </select>
        </label>

        <label className="mdc-admin-simulate__checkbox">
          <input
            type="checkbox"
            checked={executeToolsInSandbox}
            onChange={(event) => setExecuteToolsInSandbox(event.target.checked)}
          />
          <span>Executar tools em sandbox (com token do admin)</span>
        </label>

        <label className="mdc-admin-simulate__checkbox">
          <input
            type="checkbox"
            checked={generateAnswer}
            onChange={(event) => setGenerateAnswer(event.target.checked)}
          />
          <span>Gerar resposta com LLM (mais lento)</span>
        </label>

        <button
          type="button"
          className="mdc-chat-ws-toolbar-btn mdc-chat-ws-toolbar-btn--primary"
          disabled={isLoading}
          onClick={() => void handleSimulate()}
        >
          {isLoading ? "Simulando..." : "Simular agente"}
        </button>
          </article>
        </div>

        <div className="mdc-admin-split__main mdc-admin-simulate__results-pane">
      {error ? <p className="mdc-admin-simulate__error">{error}</p> : null}

      {!result && !error ? (
        <p className="mdc-chat-muted mdc-admin-simulate__placeholder">
          Execute uma simulação para ver prompt, RAG, tools e resposta prevista.
        </p>
      ) : null}

      {result ? (
        <div className="mdc-admin-simulate__results">
          <article className="mdc-admin-panel mdc-admin-simulate__card">
            <h3>Resposta</h3>
            {result.agent ? (
              <p className="mdc-chat-muted">
                Agente: <strong>{result.agent.name}</strong> ({result.agent.id})
              </p>
            ) : null}
            <pre>{result.answerPreview}</pre>
          </article>

          <article className="mdc-admin-panel mdc-admin-simulate__card">
            <h3>Prompt final (system)</h3>
            <pre>{result.finalPrompt?.preview || result.finalPrompt?.systemPrompt || "—"}</pre>
          </article>

          <div className="mdc-admin-simulate__grid">
            <article className="mdc-admin-panel mdc-admin-simulate__card">
              <h3>Diretrizes aplicadas ({result.appliedGuidelines?.length ?? 0})</h3>
              <ul>
                {(result.appliedGuidelines ?? []).map((item) => (
                  <li key={item.id}>{item.title}</li>
                ))}
              </ul>
            </article>

            <article className="mdc-admin-panel mdc-admin-simulate__card">
              <h3>Chunks usados ({result.chunks?.length ?? 0})</h3>
              <ul>
                {(result.chunks ?? []).map((chunk) => (
                  <li key={chunk.id}>
                    <strong>{chunk.title}</strong>
                    <span>{Math.round((chunk.score ?? 0) * 100)}%</span>
                    <p>{chunk.preview}</p>
                  </li>
                ))}
              </ul>
            </article>

            <article className="mdc-admin-panel mdc-admin-simulate__card">
              <h3>Tools ({result.plannedToolCalls?.length ?? 0})</h3>
              <p className="mdc-chat-muted">
                Com token válido, tools como <code>get_current_user</code> são executadas via
                Core API (/me), como no chat real.
              </p>
              {(result.plannedToolCalls ?? []).length === 0 ? (
                <p className="mdc-chat-muted">Nenhuma tool selecionada para esta pergunta.</p>
              ) : (
                <ul>
                  {result.plannedToolCalls?.map((tool) => (
                    <li key={tool.name}>
                      <strong>
                        {tool.name}{" "}
                        <span className="mdc-admin-simulate__tool-status">
                          {tool.status === "executed" ? "executada" : "prevista"}
                        </span>
                      </strong>
                      <p>{tool.reason}</p>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          </div>

          {result.comparison ? (
            <article className="mdc-admin-panel mdc-admin-simulate__card">
              <h3>Comparação de contexto</h3>
              <div className="mdc-admin-simulate__comparison">
                <div>
                  <h4>Com diretrizes</h4>
                  <p>{result.comparison.withGuidelines?.summary}</p>
                </div>
                <div>
                  <h4>Sem diretrizes</h4>
                  <p>{result.comparison.withoutGuidelines?.summary}</p>
                </div>
                <div>
                  <h4>Com RAG</h4>
                  <p>{result.comparison.withRag?.summary}</p>
                </div>
                <div>
                  <h4>Sem RAG</h4>
                  <p>{result.comparison.withoutRag?.summary}</p>
                </div>
              </div>
            </article>
          ) : null}
        </div>
      ) : null}
        </div>
      </div>
    </section>
  );
}
