import { createContext, useContext, useMemo, type ReactNode } from "react";

import { delpiUiClass } from "../../../utils/delpiUiClass";
import {
  useSessionColorScheme,
  type SessionColorScheme,
  type SessionColorSchemeState,
} from "./useSessionColorScheme";

export type QuestionnaireColorScheme = "auto" | SessionColorScheme;

const QuestionnaireColorSchemeContext =
  createContext<SessionColorSchemeState | null>(null);

/**
 * Estado de tema do escopo de questionário mais próximo (ex.: futuro botão
 * de tema no cabeçalho). Exige `QuestionnaireThemeScope` como ancestral.
 */
export function useQuestionnaireColorScheme(): SessionColorSchemeState {
  const context = useContext(QuestionnaireColorSchemeContext);
  if (!context) {
    throw new Error(
      "useQuestionnaireColorScheme must be used within QuestionnaireThemeScope",
    );
  }
  return context;
}

export type QuestionnaireThemeScopeProps = {
  /**
   * `auto` (padrão): segue `prefers-color-scheme` e permite `toggle()` em
   * memória. `"light"`/`"dark"` fixam o esquema — nesse caso `toggle()`
   * apenas atualiza o estado exposto no contexto, sem alterar a raiz.
   */
  colorScheme?: QuestionnaireColorScheme;
  /** Prefixo BEM do consumidor (dual-class com `delpi-ui-form-root`). */
  prefix?: string;
  className?: string;
  children: ReactNode;
};

/**
 * Raiz de tema do kit de formulário: emite `.delpi-ui-form-root` com
 * `data-color-scheme` resolvido e expõe o estado via contexto. Não persiste
 * escolha e não toca elementos fora da própria raiz.
 */
export function QuestionnaireThemeScope({
  colorScheme = "auto",
  prefix = "ds",
  className,
  children,
}: QuestionnaireThemeScopeProps) {
  const session = useSessionColorScheme();
  const resolved: SessionColorScheme =
    colorScheme === "auto" ? session.scheme : colorScheme;

  const contextValue = useMemo<SessionColorSchemeState>(
    () => ({
      scheme: resolved,
      toggle: session.toggle,
      userChosen: session.userChosen,
    }),
    [resolved, session.toggle, session.userChosen],
  );

  const rootClass = [
    delpiUiClass(`${prefix}-form-root`, "delpi-ui-form-root"),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <QuestionnaireColorSchemeContext.Provider value={contextValue}>
      <div className={rootClass} data-color-scheme={resolved}>
        {children}
      </div>
    </QuestionnaireColorSchemeContext.Provider>
  );
}
