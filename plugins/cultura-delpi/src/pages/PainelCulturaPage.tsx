import { useEffect, useMemo, useState } from "react";

import { getCulturaDelpiContent } from "../api/culturaDelpiApi";
import {
  CulturaCalendarIcon,
  CulturaMissionIcon,
  CulturaPurposeIcon,
  CulturaValorIcon,
  CulturaVisionIcon,
} from "../components/CulturaPanelIcons";
import {
  CULTURA_DELPI_PAGE_TITLE,
  CULTURA_DELPI_PLACEHOLDER,
  CULTURA_DELPI_SUBTITLE,
} from "../content/culturaDelpi";
import type { CulturaDelpiContent } from "../types/culturaDelpi";
import {
  displayField,
  formatUpdatedAtFooter,
  isCulturaContentEmpty,
  parseValorItem,
} from "../utils/format";

export function PainelCulturaPage() {
  const [content, setContent] = useState<CulturaDelpiContent | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadContent() {
      setLoading(true);
      setError(null);

      try {
        const data = await getCulturaDelpiContent(controller.signal);
        setContent(data);
      } catch (err) {
        if (controller.signal.aborted) return;
        const message =
          err instanceof Error
            ? err.message
            : "Não foi possível carregar o conteúdo da Cultura DELPI.";
        setError(message);
        setContent(null);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void loadContent();

    return () => controller.abort();
  }, []);

  const valores = useMemo(() => {
    if (!content) return [];
    return content.valores.map((item) => item.trim()).filter(Boolean);
  }, [content]);

  const parsedValores = useMemo(
    () => valores.map((item) => parseValorItem(item)),
    [valores],
  );

  const footerLabel = content ? formatUpdatedAtFooter(content.updatedAt) : null;

  const showProvisionalNotice = content ? isCulturaContentEmpty(content) : false;

  return (
    <div className="cultura-delpi cultura-delpi-page cultura-delpi-panel">
      <div className="cultura-delpi-panel__inner">
        <header className="cultura-delpi-panel__hero">
          <p className="cultura-delpi-panel__eyebrow">Cultura DELPI</p>
          <span className="cultura-delpi-panel__eyebrow-mark" aria-hidden="true" />
          <h1 className="cultura-delpi-panel__title">{CULTURA_DELPI_PAGE_TITLE}</h1>
          <p className="cultura-delpi-panel__subtitle">{CULTURA_DELPI_SUBTITLE}</p>
        </header>

        {loading ? (
          <div className="cultura-delpi__state" role="status" aria-live="polite">
            <p>Carregando conteúdo institucional…</p>
          </div>
        ) : null}

        {!loading && error ? (
          <div className="cultura-delpi__state cultura-delpi__state--error" role="alert">
            <p>{error}</p>
            <p className="cultura-delpi__state-hint">
              Verifique sua conexão e permissão de visualização (`cultura-delpi.view`).
            </p>
          </div>
        ) : null}

        {!loading && !error && content ? (
          <>
            {showProvisionalNotice ? (
              <div className="cultura-delpi-panel__notice" role="status">
                <p>Conteúdo provisório — aguardando definição oficial pela DELPI.</p>
              </div>
            ) : null}

            <article className="cultura-delpi-panel__purpose">
              <div className="cultura-delpi-panel__purpose-accent" aria-hidden="true" />
              <div className="cultura-delpi-panel__purpose-body">
                <div className="cultura-delpi-panel__icon-ring cultura-delpi-panel__icon-ring--lg">
                  <CulturaPurposeIcon className="cultura-delpi-panel__icon" />
                </div>
                <div className="cultura-delpi-panel__purpose-copy">
                  <p className="cultura-delpi-panel__label">Propósito</p>
                  <p className="cultura-delpi-panel__purpose-text">
                    {displayField(content.proposito)}
                  </p>
                </div>
              </div>
              <div className="cultura-delpi-panel__purpose-decor" aria-hidden="true">
                <span className="cultura-delpi-panel__purpose-dots" />
              </div>
            </article>

            <div className="cultura-delpi-panel__duo">
              <article className="cultura-delpi-panel__card">
                <div className="cultura-delpi-panel__card-accent" aria-hidden="true" />
                <div className="cultura-delpi-panel__card-body">
                  <div className="cultura-delpi-panel__icon-ring">
                    <CulturaMissionIcon className="cultura-delpi-panel__icon" />
                  </div>
                  <div className="cultura-delpi-panel__card-copy">
                    <p className="cultura-delpi-panel__label">Missão</p>
                    <p className="cultura-delpi-panel__card-text">
                      {displayField(content.missao)}
                    </p>
                  </div>
                </div>
              </article>

              <article className="cultura-delpi-panel__card">
                <div className="cultura-delpi-panel__card-accent" aria-hidden="true" />
                <div className="cultura-delpi-panel__card-body">
                  <div className="cultura-delpi-panel__icon-ring">
                    <CulturaVisionIcon className="cultura-delpi-panel__icon" />
                  </div>
                  <div className="cultura-delpi-panel__card-copy">
                    <p className="cultura-delpi-panel__label">Visão</p>
                    <p className="cultura-delpi-panel__card-text">
                      {displayField(content.visao)}
                    </p>
                  </div>
                </div>
              </article>
            </div>

            <section className="cultura-delpi-panel__values-section" aria-label="Valores">
              <p className="cultura-delpi-panel__values-heading">Valores</p>
              <div className="cultura-delpi-panel__values-shell">
                {parsedValores.length > 0 ? (
                  <div className="cultura-delpi-panel__values-grid">
                    {parsedValores.map((valor, index) => (
                      <article
                        key={`${valor.titulo}-${index}`}
                        className="cultura-delpi-panel__value-card"
                      >
                        <div className="cultura-delpi-panel__value-icon-wrap">
                          <CulturaValorIcon
                            className="cultura-delpi-panel__value-icon"
                            index={index}
                          />
                        </div>
                        {valor.titulo ? (
                          <h3 className="cultura-delpi-panel__value-title">{valor.titulo}</h3>
                        ) : null}
                        {valor.descricao ? (
                          <p className="cultura-delpi-panel__value-desc">{valor.descricao}</p>
                        ) : valor.titulo ? null : (
                          <p className="cultura-delpi-panel__value-desc">
                            {CULTURA_DELPI_PLACEHOLDER}
                          </p>
                        )}
                      </article>
                    ))}
                  </div>
                ) : (
                  <p className="cultura-delpi-panel__values-empty">{CULTURA_DELPI_PLACEHOLDER}</p>
                )}
              </div>
            </section>

            {footerLabel ? (
              <footer className="cultura-delpi-panel__footer">
                <CulturaCalendarIcon className="cultura-delpi-panel__footer-icon" />
                <p>{footerLabel}</p>
              </footer>
            ) : null}
          </>
        ) : null}
      </div>
    </div>
  );
}
