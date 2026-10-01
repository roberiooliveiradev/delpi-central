import { useEffect, useRef, useState } from "react";

import { DELIA_ROOT_CLASS, DeliaPageHeader } from "./ui/deliaUi";
import {
  DeliaInteractionError,
  buildInteractionContext,
  submitInteractionTurn,
} from "./api/interactionClient";
import type { DeliaInteractionProvenance } from "./api/interactionClient";

/** Host props from Portal AppHost — presentation/transport only. */
export type AppProps = {
  getAccessToken?: () => string | undefined;
  basePath?: string;
  pathname?: string;
  search?: string;
  alternateEntry?: string;
  appRoutes?: Array<{ path: string; entry?: string; openInNewTab?: boolean }>;
  routeLabel?: string;
  /** Frontend presentation hint only — never backend authorization authority. */
  permissions?: string[];
  /** Frontend presentation hint only — never backend authorization authority. */
  isSuperadmin?: boolean;
};

/** Transient UI display state only — not session persistence or memory. */
type DisplayTurn = {
  id: string;
  role: "user" | "delia";
  content: string;
  epistemicClass?: string | null;
  limitations?: string[];
  groundingStatus?: "GROUNDED" | "NON_GROUNDED" | null;
  provenance?: DeliaInteractionProvenance | null;
};

const TOKEN_UNAVAILABLE_MESSAGE =
  "Token de acesso indisponível. Recarregue pelo Portal.";

/**
 * C3-INTERACTION-RUNTIME-01 + C3-INTERACTION-CONTINUITY-01.
 *
 * Bounded transient multi-turn interaction: rendered turns are kept in
 * React memory only and resent as untrusted prior context on each new
 * turn. No browser storage and no backend persistence — a reload
 * resets the conversation. permissions / isSuperadmin remain host
 * presentation hints and are never sent as backend authority.
 */
export default function App({
  pathname,
  basePath,
  routeLabel,
  getAccessToken,
  permissions: _permissions,
  isSuperadmin: _isSuperadmin,
}: AppProps) {
  void _permissions;
  void _isSuperadmin;

  const hostPath = pathname || basePath || "/apps/delia";

  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<DisplayTurn[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const turnsEndRef = useRef<HTMLLIElement | null>(null);

  useEffect(() => {
    const end = turnsEndRef.current;
    if (end && typeof end.scrollIntoView === "function") {
      end.scrollIntoView({ block: "end" });
    }
  }, [turns.length, loading]);

  useEffect(
    () => () => {
      abortRef.current?.abort();
    },
    [],
  );

  async function handleSubmit() {
    const value = input.trim();
    if (!value || loading) return;
    if (!getAccessToken || !getAccessToken()) {
      setError(TOKEN_UNAVAILABLE_MESSAGE);
      return;
    }

    setLoading(true);
    setError(null);
    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const result = await submitInteractionTurn(value, {
        getAccessToken,
        signal: controller.signal,
        context: buildInteractionContext(turns),
      });
      setTurns((previous) => [
        ...previous,
        { id: result.user_turn_id, role: "user", content: value },
        {
          id: result.result_turn_id,
          role: "delia",
          content: result.content,
          epistemicClass: result.epistemic_class,
          limitations: result.limitations,
          groundingStatus: result.grounding_status,
          provenance: result.provenance,
        },
      ]);
      setInput("");
    } catch (submitError) {
      if (
        submitError instanceof Error &&
        submitError.name === "AbortError"
      ) {
        return;
      }
      setError(
        submitError instanceof DeliaInteractionError
          ? submitError.message
          : "Erro inesperado ao falar com a DÉLIA.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={`${DELIA_ROOT_CLASS} dashboard-page`}>
      <main className="delia-page-stack" aria-label="DÉLIA">
        <DeliaPageHeader
          title="DÉLIA"
          subtitle="Converse com a inteligência operacional da DELPI. A conversa é mantida apenas nesta tela e não é salva."
        />

        <section
          className="delia-interaction"
          aria-label="Interação com a DÉLIA"
        >
          {turns.length > 0 ? (
            <ul className="delia-turns" aria-label="Respostas">
              {turns.map((turn, index) => (
                <li
                  key={turn.id}
                  ref={
                    index === turns.length - 1 ? turnsEndRef : undefined
                  }
                  className={`delia-turn delia-turn--${turn.role}`}
                >
                  <span className="delia-turn__label">
                    {turn.role === "user" ? "Você" : "DÉLIA"}
                  </span>
                  <p className="delia-turn__content">{turn.content}</p>
                  {turn.epistemicClass ? (
                    <span className="delia-turn__meta">
                      classificação: {turn.epistemicClass}
                    </span>
                  ) : null}
                  {turn.groundingStatus === "GROUNDED" &&
                  turn.provenance?.source ? (
                    <span className="delia-turn__meta">
                      fonte: Cadastro de Produtos DELPI ·{" "}
                      {turn.provenance.specialist_id ?? "especialista"}/
                      {turn.provenance.protocol ?? "MCP"} ·{" "}
                      {turn.provenance.observed_at ?? ""}
                    </span>
                  ) : null}
                  {turn.limitations && turn.limitations.length > 0 ? (
                    <span className="delia-turn__meta">
                      limitações: {turn.limitations.join(", ")}
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : null}

          {error ? (
            <p className="delia-interaction__error" role="alert">
              {error}
            </p>
          ) : null}

          <form
            className="delia-interaction__form"
            onSubmit={(event) => {
              event.preventDefault();
              void handleSubmit();
            }}
          >
            <label htmlFor="delia-interaction-input">
              Pergunte à DÉLIA
            </label>
            <textarea
              id="delia-interaction-input"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Digite sua pergunta…"
              rows={3}
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !input.trim()}
            >
              {loading ? "Enviando…" : "Enviar"}
            </button>
          </form>
        </section>

        <p className="delia-host-meta">
          {routeLabel ? `${routeLabel} · ` : null}
          Contexto de host: <span>{hostPath}</span>
        </p>
      </main>
    </div>
  );
}
