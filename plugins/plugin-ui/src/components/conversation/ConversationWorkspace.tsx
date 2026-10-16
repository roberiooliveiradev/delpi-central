import type { ReactNode, Ref, UIEventHandler } from "react";

export type ConversationWorkspaceDensity = "comfortable" | "compact";

export type ConversationWorkspaceProps = {
  /** Chrome superior leve — tipicamente `ConversationHeader`. */
  header?: ReactNode;
  /** Aviso persistente acima do viewport (ex.: modo demonstração). */
  banner?: ReactNode;
  /** Conteúdo da conversa — recepção, timeline, activity pendente. */
  children: ReactNode;
  /** Rodapé ancorado — tipicamente composer + erro + helper. */
  footer?: ReactNode;
  /** Optional shared control above the anchored composer, outside the scroll viewport. */
  scrollNavigator?: ReactNode;
  /** Densidade dos paddings do workspace. */
  density?: ConversationWorkspaceDensity;
  /**
   * Ref do viewport rolável — necessário quando o consumidor faz
   * cálculo de proximidade do fundo (autoscroll). O workspace mantém
   * a propriedade do scroll; a ref é apenas de leitura.
   */
  bodyRef?: Ref<HTMLDivElement | null>;
  onBodyScroll?: UIEventHandler<HTMLDivElement>;
  className?: string;
  columnClassName?: string;
  "aria-label"?: string;
};

/**
 * Shell de conversação: header fixo + corpo rolável com coluna de
 * leitura centrada + rodapé ancorado. Apresentação pura — não conhece
 * turnos, API, auth, atividade ou estado de conversa.
 *
 * A coluna de leitura usa `flex: 1 0 auto`, então conteúdo curto
 * (recepção) cresce e pode se centrar verticalmente, enquanto conteúdo
 * alto transborda pelo scroll do corpo. O rodapé nunca rola junto.
 */
export function ConversationWorkspace({
  header,
  banner,
  children,
  footer,
  scrollNavigator,
  density = "comfortable",
  bodyRef,
  onBodyScroll,
  className,
  columnClassName,
  "aria-label": ariaLabel,
}: ConversationWorkspaceProps) {
  return (
    <section
      className={`delpi-ui-conversation-workspace delpi-ui-conversation-workspace--${density}${
        className ? ` ${className}` : ""
      }`}
      aria-label={ariaLabel}
    >
      {header ? (
        <div className="delpi-ui-conversation-workspace__header">
          {header}
        </div>
      ) : null}
      {banner ? (
        <div className="delpi-ui-conversation-workspace__banner">
          <div className="delpi-ui-conversation-workspace__banner-column">
            {banner}
          </div>
        </div>
      ) : null}
      <div
        className="delpi-ui-conversation-workspace__body"
        ref={bodyRef}
        onScroll={onBodyScroll}
      >
        <div
          className={`delpi-ui-conversation-workspace__column${
            columnClassName ? ` ${columnClassName}` : ""
          }`}
        >
          {children}
        </div>
      </div>
      {scrollNavigator ? (
        <div className="delpi-ui-conversation-workspace__scroll-navigation">
          {scrollNavigator}
        </div>
      ) : null}
      {footer ? (
        <div className="delpi-ui-conversation-workspace__footer">
          <div className="delpi-ui-conversation-workspace__footer-column">
            {footer}
          </div>
        </div>
      ) : null}
    </section>
  );
}
