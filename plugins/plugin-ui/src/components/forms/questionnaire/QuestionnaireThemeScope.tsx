import {
  createContext,
  useContext,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { delpiUiClass } from "../../../utils/delpiUiClass";
import {
  useSessionColorScheme,
  type SessionColorScheme,
  type SessionColorSchemeState,
} from "./useSessionColorScheme";

export type QuestionnaireColorScheme = "auto" | SessionColorScheme;

export type QuestionnaireColorSchemeState = SessionColorSchemeState & {
  /**
   * `true` só quando `colorScheme="auto"`: com esquema fixo (`light`/`dark`)
   * `toggle()` é no-op e o `FormThemeToggle` não deve ser exibido.
   */
  canToggle: boolean;
};

const QuestionnaireColorSchemeContext =
  createContext<QuestionnaireColorSchemeState | null>(null);

const noopToggle = () => {};

/** Duração da transição de cores da troca de tema (R26). */
export const THEME_TRANSITION_MS = 220;

function prefersReducedMotion(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches === true
  );
}

/**
 * Estado de tema do escopo de questionário mais próximo (ex.: botão
 * `FormThemeToggle` no cabeçalho). Exige `QuestionnaireThemeScope` como
 * ancestral.
 */
export function useQuestionnaireColorScheme(): QuestionnaireColorSchemeState {
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
   * memória. `"light"`/`"dark"` fixam o esquema — `canToggle` vira `false`
   * e `toggle()` não faz nada.
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
  const canToggle = colorScheme === "auto";

  const contextValue = useMemo<QuestionnaireColorSchemeState>(
    () => ({
      scheme: resolved,
      toggle: canToggle ? session.toggle : noopToggle,
      userChosen: session.userChosen,
      canToggle,
    }),
    [resolved, canToggle, session.toggle, session.userChosen],
  );

  const rootClass = [
    delpiUiClass(`${prefix}-form-root`, "delpi-ui-form-root"),
    className,
  ]
    .filter(Boolean)
    .join(" ");

  /*
   * R26 — troca suave só durante a mudança: quando `resolved` muda (toggle
   * ou aparelho), o atributo `data-theme-transition` é ligado no mesmo
   * commit visual da troca (useLayoutEffect roda antes do paint — a
   * transição declarada no CSS pós-mudança anima as cores) e removido
   * ~220 ms depois (THEME_TRANSITION_MS). No carregamento não há mudança: atributo ausente.
   * prefers-reduced-motion: troca imediata, atributo nunca ligado.
   */
  const [transitioning, setTransitioning] = useState(false);
  const appliedRef = useRef(resolved);
  useLayoutEffect(() => {
    if (appliedRef.current === resolved) return;
    appliedRef.current = resolved;
    if (prefersReducedMotion()) return;
    setTransitioning(true);
  }, [resolved]);
  useEffect(() => {
    if (!transitioning) return;
    const timer = window.setTimeout(
      () => setTransitioning(false),
      THEME_TRANSITION_MS,
    );
    return () => window.clearTimeout(timer);
  }, [transitioning]);

  return (
    <QuestionnaireColorSchemeContext.Provider value={contextValue}>
      <div
        className={rootClass}
        data-color-scheme={resolved}
        data-theme-transition={transitioning ? "" : undefined}
      >
        {children}
      </div>
    </QuestionnaireColorSchemeContext.Provider>
  );
}
