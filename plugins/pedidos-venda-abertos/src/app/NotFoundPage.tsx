import { navigatePluginView } from "./pluginNavigation.ts";
import { PVA_STATE_BOX } from "../ui/stateChrome.ts";

type NotFoundPageProps = {
  basePath: string;
};

export function NotFoundPage({ basePath }: NotFoundPageProps) {
  return (
    <div className="pva-internal-page" role="alert">
      <h1 className="pva-internal-page__title">Página não encontrada</h1>
      <p className="pva-internal-page__text">
        A rota solicitada não corresponde a uma área deste módulo.
      </p>
      <div className={`${PVA_STATE_BOX} pva-checkup__actions`}>
        <button
          type="button"
          className="pva-btn pva-btn--ghost"
          onClick={() => navigatePluginView("customers", { basePath })}
        >
          Voltar para Clientes
        </button>
        <button
          type="button"
          className="pva-btn pva-btn--ghost"
          onClick={() => navigatePluginView("orders", { basePath })}
        >
          Voltar para Pedidos em aberto
        </button>
      </div>
    </div>
  );
}
