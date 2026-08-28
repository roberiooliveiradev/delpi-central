import { resolveUserFirstName } from "../utils/authFirstName";
import { copy } from "../content/copy";

export type PpcLiquidLoadingSize = "sm" | "md" | "lg";

type Props = {
  /** Sobrescreve o texto; se omitido, usa copy + primeiro nome do JWT. */
  message?: string;
  /** Diâmetro do orbe. Default: `md` (120px). */
  size?: PpcLiquidLoadingSize;
  className?: string;
};

/**
 * Loader circular reutilizável do Portal PCP — orbe “voice” com gradiente
 * fluido (azul / ciano / roxo), pulsação e brilho. Escopo do plugin para
 * avaliação antes de eventual promoção ao kit.
 */
export function PpcLiquidLoading({ message, size = "md", className }: Props) {
  const firstName = resolveUserFirstName();
  const text =
    message ??
    (firstName ? copy.reports.liquidLoadingNamed(firstName) : copy.reports.liquidLoading);

  const rootClass = ["ppc-liquid-loading", `ppc-liquid-loading--${size}`, className]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass} role="status" aria-live="polite" aria-busy="true">
      <div className="ppc-liquid-loading__stage" aria-hidden="true">
        <span className="ppc-liquid-loading__glow" />
        <div className="ppc-liquid-loading__orb">
          <span className="ppc-liquid-loading__mesh" />
          <span className="ppc-liquid-loading__blob ppc-liquid-loading__blob--violet" />
          <span className="ppc-liquid-loading__blob ppc-liquid-loading__blob--cyan" />
          <span className="ppc-liquid-loading__blob ppc-liquid-loading__blob--navy" />
          <span className="ppc-liquid-loading__blob ppc-liquid-loading__blob--sky" />
          <span className="ppc-liquid-loading__blob ppc-liquid-loading__blob--flare" />
          <span className="ppc-liquid-loading__specular" />
          <span className="ppc-liquid-loading__rim" />
        </div>
      </div>
      <p className="ppc-liquid-loading__message">{text}</p>
    </div>
  );
}
