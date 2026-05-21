import { useEffect, useState } from "react";
import type { AppProps } from "../../App";
import { fetchTransformometroHealth } from "../../data/api/transformometroHealthApi";
import "./HomePage.css";

type LoadState = "loading" | "ok" | "error";

type HomeProps = Pick<AppProps, "getAccessToken"> & {
  onGoProcessos?: () => void;
};

export function HomePage({ getAccessToken, onGoProcessos }: HomeProps) {
  const [state, setState] = useState<LoadState>("loading");
  const [detail, setDetail] = useState<string>("");

  useEffect(() => {
    let cancelled = false;

    fetchTransformometroHealth(getAccessToken)
      .then((payload) => {
        if (cancelled) return;
        setState("ok");
        setDetail(JSON.stringify(payload, null, 2));
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setState("error");
        setDetail(error instanceof Error ? error.message : "Erro desconhecido");
      });

    return () => {
      cancelled = true;
    };
  }, [getAccessToken]);

  return (
    <div className="tm-home">
      <header className="tm-home__header">
        <h1>Transformômetro</h1>
        <p className="tm-home__subtitle">
          Melhorias de processo — economia, investimento, ROI e payback.
        </p>
      </header>

      <section className="tm-home__card">
        <h2>Fase 1 — cadastro</h2>
        <p>
          API com CRUD de processos, revisões, medições, investimentos e recursos no
          PostgreSQL. Use o cadastro para substituir a planilha.
        </p>

        {onGoProcessos ? (
          <p>
            <button type="button" className="tm-home__link" onClick={onGoProcessos}>
              Abrir lista de processos →
            </button>
          </p>
        ) : null}

        <div className={`tm-home__status tm-home__status--${state}`}>
          {state === "loading" && "Verificando API…"}
          {state === "ok" && "API online"}
          {state === "error" && "Falha ao conectar na API"}
        </div>

        {detail ? (
          <pre className="tm-home__pre" aria-label="Resposta da API">
            {detail}
          </pre>
        ) : null}
      </section>
    </div>
  );
}
