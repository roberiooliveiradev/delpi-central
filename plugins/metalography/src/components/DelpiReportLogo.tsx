import logoOnDarkUrl from "../assets/delpi-logo-on-dark.png";
import logoOnLightUrl from "../assets/delpi-logo.png";
import { usePortalColorScheme } from "../theme/portalColorScheme";

/**
 * Marca Delpi do relatório.
 * Fundo claro: PNG documental (`delpi-logo.png`).
 * Fundo escuro: a mesma arte da marca, também arquivada em
 * `tv-dashboard-api/tv_app/content/brand/logoDelpiOnDark.png`.
 * O arquivo local `delpi-logo-on-dark.png` é a cópia usada por este MFE.
 * A impressão isolada lê `data-print-src` e volta à logo clara.
 */

export function DelpiReportLogo({ id, alt }: { id?: string; alt: string }) {
  const onDark = usePortalColorScheme() === "dark";
  return (
    <img
      id={id}
      src={onDark ? logoOnDarkUrl : logoOnLightUrl}
      data-brand-logo="delpi"
      data-print-src={logoOnLightUrl}
      alt={alt}
    />
  );
}
