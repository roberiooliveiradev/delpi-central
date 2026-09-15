import { ensureComunicadoDualClass } from "@delpi/plugin-ui/index";

import { ComunicadoMediaPlaceholder } from "./ComunicadoMediaPlaceholder";

type Props = {
  /** Quando false, não renderiza (já há metadados / frame). */
  visible: boolean;
  className?: string;
};

/**
 * Overlay “Carregando vídeo…” sobre o `<video>` — editor e apresentação.
 * Não desmonta o media element (o stream continua).
 */
export function ComunicadoVideoLoadOverlay({ visible, className = "" }: Props) {
  if (!visible) return null;
  return (
    <div
      className={ensureComunicadoDualClass(
        ["tdp-presentation-video__load-overlay", className].filter(Boolean).join(" "),
      )}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <ComunicadoMediaPlaceholder kind="video" state="loading" />
    </div>
  );
}
