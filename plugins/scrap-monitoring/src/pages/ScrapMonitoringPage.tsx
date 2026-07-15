import {
  branchRouteFromPathname,
  BRANCH_ROUTE_LABELS,
  totvsBranchFromRoute,
} from "../constants/branches";

type Props = {
  pathname: string;
};

/**
 * Scaffold — UI completa (KPIs/gráficos/tabela) na fase seguinte.
 * Nesta entrega: rotas SC/ES + mapeamento para filial TOTVS 01/02.
 */
export function ScrapMonitoringPage({ pathname }: Props) {
  const branchRoute = branchRouteFromPathname(pathname);
  const filial = totvsBranchFromRoute(branchRoute);
  const label = BRANCH_ROUTE_LABELS[branchRoute];

  return (
    <div className="dashboard-scrap-monitoring dashboard-page">
      <header className="sm-header">
        <h1 className="sm-title">Acompanhamento de Refugos — {label}</h1>
        <p className="sm-subtitle">
          Filial TOTVS <strong>{filial}</strong> · API <code>/refugos</code>
        </p>
      </header>

      <section className="sm-card" aria-live="polite">
        <h2 className="sm-card__title">Em construção</h2>
        <p className="sm-card__body">
          O backend já expõe <code>/refugos/resumo</code>, <code>/refugos/rankings</code>,{" "}
          <code>/refugos/registros</code> e <code>/refugos/filtros</code>. A UI dos painéis
          (KPIs, gráficos e tabela) será ligada a essas rotas na próxima fase.
        </p>
      </section>
    </div>
  );
}
