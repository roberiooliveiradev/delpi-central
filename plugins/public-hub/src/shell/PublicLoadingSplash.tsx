type PublicLoadingSplashProps = {
  /** Chrome do palco — kiosk usa visual cinematográfico em tela cheia. */
  chrome?: "default" | "kiosk" | "fullpage";
  label?: string;
};

/**
 * Splash de carregamento transversal do hub público (forms, TV kiosk, etc.).
 * Centralizado na viewport; não depende de layout externo para alinhar.
 * No chrome default/fullpage a marca já vem do Stage — só o orbit.
 */
export function PublicLoadingSplash({
  chrome = "default",
  label = "Carregando",
}: PublicLoadingSplashProps) {
  const isKiosk = chrome === "kiosk";
  const rootClass = isKiosk
    ? "pub-splash pub-splash--kiosk"
    : "pub-splash";

  return (
    <div
      className={rootClass}
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label={label}
    >
      <div className="pub-splash__glow" aria-hidden="true" />
      <div className="pub-splash__stage">
        <div className="pub-splash__orbit" aria-hidden="true">
          <span className="pub-splash__ring" />
          <span className="pub-splash__ring pub-splash__ring--delayed" />
          <span className="pub-splash__core" />
        </div>
        <p className="pub-splash__label">{label}</p>
        <div className="pub-splash__bar" aria-hidden="true">
          <span className="pub-splash__bar-fill" />
        </div>
      </div>
    </div>
  );
}
