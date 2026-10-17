import { Blocks, ExternalLink } from "lucide-react";

/** Display-only projection from the Portal/Core's approved application catalog. */
export type PluginNavigationItem = {
  id: string;
  title: string;
  description?: string;
  selected?: boolean;
  /** Display hint from an approved navigation contract, NOT permission. */
  external?: boolean;
};

export type PluginNavigationProps = {
  /** This UI does not authorize apps. Only an authorized consumer supplies ready. */
  status?: "contract_unavailable" | "ready" | "loading" | "authorized_empty" | "error";
  items?: readonly PluginNavigationItem[];
  /** Intent to navigate by opaque identity; host resolves official route + live AuthZ. */
  onOpenApplication?: (id: string) => void;
  onRetry?: () => void;
  className?: string;
};

/**
 * Presentation only. No local app registry, deep links, provider discovery,
 * installation, permission inference or execution of MCP/A2A capabilities.
 */
export function PluginNavigation({
  status = "contract_unavailable",
  items = [],
  onOpenApplication,
  onRetry,
  className,
}: PluginNavigationProps) {
  return (
    <div className={["delpi-ui-plugin-navigation", className].filter(Boolean).join(" ")} data-state={status}>
      {status === "contract_unavailable" ? (
        <p className="delpi-ui-plugin-navigation__message">
          Aplicações estarão disponíveis após a integração autorizada com o Portal.
        </p>
      ) : status === "loading" ? (
        <p className="delpi-ui-plugin-navigation__message" role="status">Carregando aplicações…</p>
      ) : status === "authorized_empty" ? (
        <p className="delpi-ui-plugin-navigation__message">Nenhuma aplicação disponível.</p>
      ) : status === "error" ? (
        <div className="delpi-ui-plugin-navigation__feedback">
          <p className="delpi-ui-plugin-navigation__message" role="alert">Não foi possível carregar aplicações.</p>
          {onRetry ? (
            <button type="button" className="delpi-ui-plugin-navigation__retry" onClick={onRetry}>
              Tentar novamente
            </button>
          ) : null}
        </div>
      ) : status === "ready" && onOpenApplication && items.length > 0 ? (
        <section aria-label="Aplicações disponíveis">
          <h2 className="delpi-ui-conversation-sidebar__section-heading">Disponíveis para você</h2>
          <ul className="delpi-ui-plugin-navigation__list">
            {items.map(item => (
              <li key={item.id}>
                <button
                  type="button"
                  className="delpi-ui-plugin-navigation__item"
                  aria-label={item.title}
                  aria-current={item.selected ? "page" : undefined}
                  onClick={() => onOpenApplication(item.id)}
                >
                  <Blocks size={19} strokeWidth={1.8} aria-hidden="true" />
                  <span className="delpi-ui-plugin-navigation__details">
                    <span className="delpi-ui-plugin-navigation__title">{item.title}</span>
                    {item.description ? (
                      <span className="delpi-ui-plugin-navigation__description">{item.description}</span>
                    ) : null}
                  </span>
                  {item.external ? <ExternalLink size={15} strokeWidth={1.8} aria-hidden="true" /> : null}
                </button>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
