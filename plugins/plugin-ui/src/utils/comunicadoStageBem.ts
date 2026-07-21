import { delpiUiClass } from "./delpiUiClass";

/** Prefixo legado do MFE / presentation (ainda no DOM para seletores do editor). */
export const COMUNICADO_LEGACY_PREFIX = "tdp-comunicado";
/** Prefixo canônico estilizado em `styles/comunicado-stage.css`. */
export const COMUNICADO_UI_PREFIX = "delpi-ui-comunicado";

/**
 * Expande tokens `tdp-comunicado*` → dual-class com `delpi-ui-comunicado*`.
 * Outros tokens (ex.: `tdp-native-screen`, `td-composer__*`) passam intactos.
 */
export function ensureComunicadoDualClass(className: string | undefined): string {
  const raw = (className ?? "").trim();
  if (!raw) return "";
  const tokens = raw.split(/\s+/).filter(Boolean);
  const out: string[] = [];
  const seen = new Set<string>();
  const push = (token: string) => {
    if (seen.has(token)) return;
    seen.add(token);
    out.push(token);
  };
  for (const token of tokens) {
    push(token);
    if (token.startsWith(COMUNICADO_LEGACY_PREFIX)) {
      push(`${COMUNICADO_UI_PREFIX}${token.slice(COMUNICADO_LEGACY_PREFIX.length)}`);
    }
  }
  return out.join(" ");
}

/** Dual-class para um sufixo BEM (`""`, `"__block"`, `"__block--heading"`, …). */
export function comunicadoDualSuffix(suffix: string): string {
  return delpiUiClass(
    `${COMUNICADO_LEGACY_PREFIX}${suffix}`,
    `${COMUNICADO_UI_PREFIX}${suffix}`,
  );
}

export type ComunicadoStageBemClassNames = {
  /** `tdp-native-screen` + dual root do comunicado. */
  root: string;
  stage: string;
  masterLogo: string;
  block: string;
  link: string;
  visualBox: string;
};

/**
 * Classes BEM do palco de slide personalizado.
 * CSS canônico: `.delpi-ui-comunicado*` em `comunicado-stage.css`.
 */
export function comunicadoStageBemClasses(prefix = "tdp"): ComunicadoStageBemClassNames {
  const legacyRoot = `${prefix}-comunicado`;
  return {
    root: `${prefix}-native-screen ${delpiUiClass(legacyRoot, COMUNICADO_UI_PREFIX)}`,
    stage: delpiUiClass(`${legacyRoot}__stage`, `${COMUNICADO_UI_PREFIX}__stage`),
    masterLogo: delpiUiClass(`${legacyRoot}__master-logo`, `${COMUNICADO_UI_PREFIX}__master-logo`),
    block: delpiUiClass(`${legacyRoot}__block`, `${COMUNICADO_UI_PREFIX}__block`),
    link: delpiUiClass(`${legacyRoot}__link`, `${COMUNICADO_UI_PREFIX}__link`),
    visualBox: delpiUiClass(`${legacyRoot}__visual-box`, `${COMUNICADO_UI_PREFIX}__visual-box`),
  };
}
