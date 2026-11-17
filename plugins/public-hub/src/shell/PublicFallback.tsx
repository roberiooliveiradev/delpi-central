type PublicFallbackKind = "not-found" | "error";

type PublicFallbackProps = {
  kind: PublicFallbackKind;
  /** Mensagem contextual (ex.: programação desativada). */
  message?: string;
  /** Título opcional; senão usa padrão por `kind`. */
  title?: string;
  /** `kiosk` (TV) usa composição em tela cheia com marca — o Stage kiosk não exibe logo. */
  chrome?: "default" | "kiosk" | "fullpage";
  /** Falha de chunk após deploy — botão força nova recuperação. */
  showRetry?: boolean;
  onRetry?: () => void;
};

const DEFAULT_TITLE: Record<PublicFallbackKind, string> = {
  "not-found": "Página não encontrada",
  error: "Não foi possível exibir",
};

const DEFAULT_MESSAGE: Record<PublicFallbackKind, string> = {
  "not-found": "Este link não está mais disponível.",
  error: "Erro inesperado.",
};

const HINT: Record<PublicFallbackKind, string> = {
  "not-found": "Confirme o link com quem gerencia a programação ou peça um novo endereço.",
  error: "Atualize a página em instantes. Se o problema continuar, avise o suporte DELPI.",
};

/**
 * Estado transversal not-found / erro do shell público.
 * Em kiosk (TV) traz marca Minha DELPI em destaque — o palco kiosk não exibe logo no Stage.
 */
export function PublicFallback({
  kind,
  message,
  title,
  chrome = "default",
  showRetry = false,
  onRetry,
}: PublicFallbackProps) {
  const isImmersive = chrome === "kiosk";
  const resolvedTitle = title?.trim() || DEFAULT_TITLE[kind];
  const resolvedMessage = message?.trim() || DEFAULT_MESSAGE[kind];
  const rootClass = [
    "pub-fallback",
    isImmersive ? "pub-fallback--immersive" : null,
    kind === "error" ? "pub-fallback--error" : "pub-fallback--not-found",
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass} role="alert" aria-live="polite">
      <div className="pub-fallback__glow" aria-hidden="true" />
      <div className="pub-fallback__stage">
        {isImmersive ? (
          <div className="pub-fallback__brand">
            <div className="pub-fallback__badge" aria-hidden="true">
              <img src="/p/logoMinhaDelpi.svg" alt="" draggable={false} />
            </div>
            <p className="pub-fallback__product">Minha DELPI</p>
          </div>
        ) : null}
        <h1 className="pub-fallback__title">{resolvedTitle}</h1>
        <p className="pub-fallback__message">{resolvedMessage}</p>
        <p className="pub-fallback__hint">{HINT[kind]}</p>
        {showRetry && onRetry ? (
          <button type="button" className="pub-fallback__retry" onClick={onRetry}>
            Tentar novamente
          </button>
        ) : null}
      </div>
    </div>
  );
}
