import type { ReactNode } from "react";

type Props = {
  title: string;
  hint?: string;
  badge?: string;
  children: ReactNode;
  className?: string;
  /** Dentro de abas: sem card duplicado, só título + conteúdo */
  embedded?: boolean;
};

export function CadastroSection({
  title,
  hint,
  badge,
  children,
  className,
  embedded = false,
}: Props) {
  return (
    <section
      className={[
        "ds-cadastro-section",
        embedded ? "ds-cadastro-section--embedded" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
    >
      <header className="ds-cadastro-section__header">
        <div>
          <h3 className="ds-section-title">{title}</h3>
          {hint ? <p className="ds-hint">{hint}</p> : null}
        </div>
        {badge ? <span className="ds-cadastro-section__badge">{badge}</span> : null}
      </header>
      <div className="ds-cadastro-section__body">{children}</div>
    </section>
  );
}
