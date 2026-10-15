import type { ElementType, ReactNode } from "react";

export type ConversationHeaderProps = {
  /** Nome da conversa/produto — ex.: "DÉLIA". */
  title: ReactNode;
  /** Contexto curto opcional — some em containers estreitos. */
  subtitle?: ReactNode;
  /** Identidade visual opcional à esquerda (ex.: UnifiedAvatar). */
  leading?: ReactNode;
  /** Ações opcionais à direita — o consumidor decide quais existem. */
  actions?: ReactNode;
  /** Variante compacta reduz a altura do chrome. */
  compact?: boolean;
  /** Elemento do título — "h1" quando o header é o título da página. */
  titleAs?: ElementType;
  className?: string;
};

/**
 * Chrome conversacional leve: título + subtítulo + leading + actions.
 * Mais contido que `PageHeader` (sem eyebrow/nav/refresh/meta chips) —
 * a hierarquia visual cede à conversa. Não conhece navegação, sessão,
 * identidade nem estado operacional.
 */
export function ConversationHeader({
  title,
  subtitle,
  leading,
  actions,
  compact = false,
  titleAs: Title = "h1",
  className,
}: ConversationHeaderProps) {
  return (
    <div
      className={`delpi-ui-conversation-header${
        compact ? " delpi-ui-conversation-header--compact" : ""
      }${className ? ` ${className}` : ""}`}
    >
      {leading ? (
        <div className="delpi-ui-conversation-header__leading">
          {leading}
        </div>
      ) : null}
      <div className="delpi-ui-conversation-header__content">
        <Title className="delpi-ui-conversation-header__title">
          {title}
        </Title>
        {subtitle ? (
          <p className="delpi-ui-conversation-header__subtitle">
            {subtitle}
          </p>
        ) : null}
      </div>
      {actions ? (
        <div className="delpi-ui-conversation-header__actions">
          {actions}
        </div>
      ) : null}
    </div>
  );
}
