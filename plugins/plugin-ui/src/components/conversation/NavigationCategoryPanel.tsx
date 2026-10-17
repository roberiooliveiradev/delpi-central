import type { ReactNode } from "react";
import type { NavigationRailCategory } from "./NavigationRail";

export type NavigationCategoryPanelState =
  | "ready"
  | "contract_unavailable"
  | "loading"
  | "authorized_empty"
  | "error";

export type NavigationCategoryPanelProps = {
  category: NavigationRailCategory;
  state?: NavigationCategoryPanelState;
  /** Render-only contents supplied by a legitimate consumer. */
  children?: ReactNode;
  /** Optional action already authorized by the host, never inferred from data. */
  onRetry?: () => void;
  className?: string;
};

const CATEGORY_LABELS: Record<NavigationRailCategory, string> = {
  conversations: "Conversas",
  projects: "Projetos",
  agents: "Agentes",
  plugins: "Plugins",
};

/**
 * Shared body for the existing left navigation shell.
 * The shell owns the landmark, heading and its single expand/collapse button.
 * This component never fetches or fabricates data, routes or permissions.
 */
export function NavigationCategoryPanel({
  category,
  state = "ready",
  children,
  onRetry,
  className,
}: NavigationCategoryPanelProps) {
  const label = CATEGORY_LABELS[category];
  return (
    <section
      className={["delpi-ui-navigation-category-panel", className].filter(Boolean).join(" ")}
      aria-label={label}
      data-category={category}
      data-state={state}
    >
      {state === "ready" ? (
        <div className="delpi-ui-navigation-category-panel__content">{children}</div>
      ) : state === "loading" ? (
        <p className="delpi-ui-navigation-category-panel__message" role="status">
          Carregando {label.toLocaleLowerCase("pt-BR")}…
        </p>
      ) : state === "authorized_empty" ? (
        <p className="delpi-ui-navigation-category-panel__message">
          Nenhum conteúdo disponível nesta categoria.
        </p>
      ) : state === "error" ? (
        <div className="delpi-ui-navigation-category-panel__feedback">
          <p className="delpi-ui-navigation-category-panel__message" role="alert">
            Não foi possível carregar esta categoria.
          </p>
          {onRetry ? (
            <button type="button" className="delpi-ui-navigation-category-panel__retry" onClick={onRetry}>
              Tentar novamente
            </button>
          ) : null}
        </div>
      ) : (
        <p className="delpi-ui-navigation-category-panel__message">
          Esta categoria estará disponível após sua integração.
        </p>
      )}
    </section>
  );
}
