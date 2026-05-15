import { useState } from "react";

import type { AdminRagTestResponse } from "../../../../data/api/adminTypes";
import type { GuidelineBackendPlaceholders } from "./guidelineTypes";

import "./GuidelineTestPanel.css";

type GuidelineTestPanelProps = Pick<GuidelineBackendPlaceholders, "testGuidelines">;

type SourceVisualKind = "global" | "guideline" | "attachment" | "tool";

function getSourceVisualKind(sourceType?: string | null): SourceVisualKind {
  const normalized = String(sourceType ?? "").toLowerCase();

  if (
    normalized.includes("diretriz") ||
    normalized.includes("guideline") ||
    normalized.includes("admin_guideline")
  ) {
    return "guideline";
  }

  if (
    normalized.includes("attachment") ||
    normalized.includes("session_source") ||
    normalized.includes("chat_attachment") ||
    normalized.includes("anexo")
  ) {
    return "attachment";
  }

  if (
    normalized.includes("tool") ||
    normalized.includes("action") ||
    normalized.includes("external_action") ||
    normalized.includes("ferramenta")
  ) {
    return "tool";
  }

  return "global";
}

function getSourceVisualLabel(sourceType?: string | null): string {
  const kind = getSourceVisualKind(sourceType);

  if (kind === "guideline") {
    return "Diretriz";
  }

  if (kind === "attachment") {
    return "Anexo";
  }

  if (kind === "tool") {
    return "Ferramenta";
  }

  return "Conhecimento";
}

export function GuidelineTestPanel({ testGuidelines }: GuidelineTestPanelProps) {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AdminRagTestResponse | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleTest() {
    const normalizedQuestion = question.trim();

    if (!normalizedQuestion || !testGuidelines || isTesting) {
      return;
    }

    setIsTesting(true);
    setError(null);
    setResult(null);

    try {
      const response = await testGuidelines(normalizedQuestion);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao testar diretrizes.");
    } finally {
      setIsTesting(false);
    }
  }

  const appliedGuidelines = result?.appliedGuidelines ?? result?.triggeredGuidelines ?? [];

  return (
    <article className="mdc-guideline-test-panel">
      <div className="mdc-guideline-test-panel__form">
        <div>
          <p className="mdc-chat-eyebrow">Validação</p>
          <h2>Teste de assertividade</h2>
        </div>

        <p className="mdc-chat-muted">
          Simule perguntas para validar se a base global e as diretrizes estão orientando a resposta.
        </p>

        <textarea
          value={question}
          rows={6}
          placeholder="Ex.: Como o chat deve responder quando não encontrar fonte suficiente?"
          onChange={(event) => setQuestion(event.target.value)}
        />

        <button
          type="button"
          disabled={!question.trim() || !testGuidelines || isTesting}
          onClick={() => {
            void handleTest();
          }}
        >
          {isTesting ? "Testando..." : "Testar diretrizes"}
        </button>

        {error ? (
          <div className="mdc-guideline-test-panel__error" role="alert">
            {error}
          </div>
        ) : null}
      </div>

      {result ? (
        <section className="mdc-guideline-test-panel__result">
          <header className="mdc-guideline-test-panel__result-header">
            <div>
              <p className="mdc-chat-eyebrow">Resultado</p>
              <h3>Explicabilidade do teste</h3>
            </div>

            <strong>{Math.round(result.score * 100)}%</strong>
          </header>

          <div className="mdc-guideline-test-panel__result-grid">
            <article>
              <h4>Diretrizes aplicadas</h4>
              {appliedGuidelines.length === 0 ? (
                <p>Nenhuma diretriz ativa aplicada neste teste.</p>
              ) : (
                <ul>
                  {appliedGuidelines.map((guideline) => (
                    <li key={guideline.id}>
                      <div>
                        <strong>{guideline.title}</strong>
                        {guideline.description ? <small>{guideline.description}</small> : null}
                      </div>
                      <span>{guideline.category ?? "global"}</span>
                    </li>
                  ))}
                </ul>
              )}
            </article>

            <article>
              <h4>Documentos acionados</h4>
              {result.matchedDocuments.length === 0 ? (
                <p>Nenhum documento encontrado.</p>
              ) : (
                <ul>
                  {result.matchedDocuments.map((document) => (
                    <li key={document.id}>
                      <div>
                        <strong>{document.title}</strong>
                        <small>{getSourceVisualLabel(document.sourceType)}</small>
                      </div>
                      <span
                        className={`is-${getSourceVisualKind(document.sourceType)}`}
                      >
                        {Math.round(document.score * 100)}%
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          </div>

          {result.debugContext ? (
            <article className="mdc-guideline-test-panel__debug">
              <div>
                <h4>Contexto seguro</h4>
                <span>
                  {result.debugContext.guidelineCount} diretriz(es) ·{" "}
                  {result.debugContext.documentCount} documento(s) ·{" "}
                  {result.debugContext.chunkCount} chunk(s)
                </span>
              </div>

              <dl>
                <div>
                  <dt>RAG</dt>
                  <dd>{result.debugContext.hasRagContext ? "Com contexto" : "Sem contexto"}</dd>
                </div>
                <div>
                  <dt>Diretrizes</dt>
                  <dd>
                    {result.debugContext.hasActiveGuidelines
                      ? "Aplicadas"
                      : "Nenhuma ativa"}
                  </dd>
                </div>
                <div>
                  <dt>Escopo</dt>
                  <dd>
                    {result.debugContext.filters.includeGlobal
                      ? "Base global"
                      : "Escopo restrito"}
                  </dd>
                </div>
              </dl>

              <pre>{result.debugContext.safeContextPreview}</pre>
            </article>
          ) : null}

          {result.comparison ? (
            <article className="mdc-guideline-test-panel__comparison">
              <h4>Comparação de contexto</h4>

              <div>
                <section>
                  <strong>Com diretrizes</strong>
                  <span>{result.comparison.withGuidelines.guidelineCount}</span>
                  <p>{result.comparison.withGuidelines.summary}</p>
                </section>

                <section>
                  <strong>Sem diretrizes</strong>
                  <span>{result.comparison.withoutGuidelines.guidelineCount}</span>
                  <p>{result.comparison.withoutGuidelines.summary}</p>
                </section>

                <section>
                  <strong>Com RAG</strong>
                  <span>{result.comparison.withRag.chunkCount}</span>
                  <p>{result.comparison.withRag.summary}</p>
                </section>

                <section>
                  <strong>Sem RAG</strong>
                  <span>{result.comparison.withoutRag.chunkCount}</span>
                  <p>{result.comparison.withoutRag.summary}</p>
                </section>
              </div>
            </article>
          ) : null}

          <article className="mdc-guideline-test-panel__preview">
            <h4>Prévia da resposta</h4>
            <p>{result.answerPreview}</p>
          </article>

          <article>
            <h4>Chunks usados</h4>
            {!result.chunks || result.chunks.length === 0 ? (
              <p>Nenhum chunk retornado.</p>
            ) : (
              <div className="mdc-guideline-test-panel__chunks">
                {result.chunks.map((chunk) => (
                  <section key={chunk.id}>
                    <div>
                      <strong>{chunk.title}</strong>
                      <span
                        className={`is-${getSourceVisualKind(chunk.sourceType)}`}
                      >
                        {getSourceVisualLabel(chunk.sourceType)} ·{" "}
                        {Math.round(chunk.score * 100)}%
                      </span>
                    </div>
                    <p>{chunk.preview}</p>
                  </section>
                ))}
              </div>
            )}
          </article>
        </section>
      ) : null}
    </article>
  );
}
