import { useEffect, useMemo, useState } from "react";
import {
  ArrowRight,
  Building2,
  MapPin,
  Search,
} from "lucide-react";

import { HttpRequestError } from "../api/httpClient";
import { fetchBudgetContext } from "../api/budgetPlanningApi";
import type { BudgetContext } from "../types/budgetPlanning";
import { CapexMyCostCentersPage } from "./CapexMyCostCentersPage";
import { PersonnelBudgetPage } from "./PersonnelBudgetPage";
import { CostCenterCockpit } from "../components/CostCenterCockpit";
import { PageShell } from "../components/PageShell";
import { LoadingActivityCard, StateBox } from "../components/uiKit";
import { usePermissions } from "../hooks/usePermissions";
import {
  fetchMyCostCenterPortfolio,
  type CostCenterPortfolioItem,
} from "../utils/costCenterPortfolio";
import { resolveCostCenterIcon } from "../utils/costCenterIcons";
import {
  branchCityLabel,
  formatCostCenterLabel,
  matchesCostCenterSearch,
} from "../utils/orgCostCenters";
import {
  hasCapexSubmitAccess,
  hasPersonnelEditAccess,
  hasPersonnelViewAccess,
} from "../utils/permissions";
import {
  centrosHref,
  readQueryParam,
  routeHref,
} from "../utils/routing";

function exerciseYearLabel(ctx: BudgetContext | null): string {
  const ex = ctx?.exercise;
  if (!ex) return "Ciclo";
  return String(ex.year);
}

function exerciseNameLabel(ctx: BudgetContext | null): string {
  return ctx?.exercise?.name?.trim() || "Planejamento orçamentário";
}

function cardTitle(row: CostCenterPortfolioItem): string {
  const name = String(row.cost_center_name || "").trim();
  return name || row.cost_center_id;
}

function cardLocation(row: CostCenterPortfolioItem): string {
  return branchCityLabel(row.branch ?? row.unit_id);
}

export function CostCenterBudgetPage() {
  const selectedCc = readQueryParam("cost_center_id");
  const selectedUnit = readQueryParam("unit_id");
  const { profile } = usePermissions();
  const canCapexPerm = hasCapexSubmitAccess(profile);
  const canPersonnelPerm =
    hasPersonnelViewAccess(profile) || hasPersonnelEditAccess(profile);

  const [context, setContext] = useState<BudgetContext | null>(null);
  const [portfolio, setPortfolio] = useState<CostCenterPortfolioItem[]>([]);
  const [bootLoading, setBootLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    setBootLoading(true);
    setError(null);
    fetchBudgetContext(controller.signal)
      .then(async (ctx) => {
        setContext(ctx);
        if (!ctx.exercise || !ctx.modules_unlocked) {
          setPortfolio([]);
          return;
        }
        const items = await fetchMyCostCenterPortfolio(
          ctx.exercise.id,
          controller.signal,
        );
        if (!controller.signal.aborted) setPortfolio(items);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        if (err instanceof HttpRequestError && err.status === 401) {
          setError("Sessão expirada (401). Faça login novamente.");
        } else if (err instanceof HttpRequestError && err.status === 403) {
          setError("Acesso negado aos seus centros de custo.");
        } else {
          setError(err instanceof Error ? err.message : "Erro ao carregar centros.");
        }
        setPortfolio([]);
      })
      .finally(() => {
        if (!controller.signal.aborted) setBootLoading(false);
      });
    return () => controller.abort();
  }, []);

  const selectedItem =
    selectedCc &&
    portfolio.find(
      (p) =>
        p.cost_center_id === selectedCc &&
        (!selectedUnit || p.unit_id === selectedUnit),
    );

  const modulesUnlocked = Boolean(context?.modules_unlocked);
  const showCapexSection =
    Boolean(selectedCc) &&
    canCapexPerm &&
    (selectedItem ? selectedItem.canCapex : true);
  const showPersonnelSection =
    Boolean(selectedCc) &&
    canPersonnelPerm &&
    (selectedItem ? selectedItem.canPersonnel : true);

  const filteredPortfolio = useMemo(() => {
    return portfolio.filter((row) =>
      matchesCostCenterSearch(
        {
          branch: row.branch ?? row.unit_id,
          code: row.cost_center_id,
          name: row.cost_center_name ?? undefined,
          description: row.area_id ?? undefined,
        },
        search,
      ),
    );
  }, [portfolio, search]);

  if (selectedCc) {
    const titleLabel = selectedItem
      ? String(selectedItem.cost_center_name || "").trim() ||
        formatCostCenterLabel({
          branch: selectedItem.branch ?? selectedItem.unit_id,
          code: selectedItem.cost_center_id,
          name: selectedItem.cost_center_name,
        })
      : `Centro ${selectedCc}`;
    const locationLabel = selectedItem
      ? cardLocation(selectedItem)
      : branchCityLabel(selectedUnit || undefined);

    return (
      <PageShell title={titleLabel} backHref={centrosHref()}>
        {bootLoading ? (
          <LoadingActivityCard title="Abrindo o centro…" variant="panel" />
        ) : null}
        {error ? (
          <StateBox variant="error" dismissible={false}>
            {error}
          </StateBox>
        ) : null}
        {!bootLoading && !modulesUnlocked ? (
          <StateBox variant="warning" dismissible={false}>
            Confirme a leitura das orientações antes de elaborar.{" "}
            <a href={routeHref("orientacoes")}>Ir para Orientações</a>
          </StateBox>
        ) : null}
        {!bootLoading && modulesUnlocked && (showCapexSection || showPersonnelSection) ? (
          <CostCenterCockpit
            title={titleLabel}
            locationLabel={locationLabel}
            cycleYear={exerciseYearLabel(context)}
            costCenterId={selectedCc}
            unitId={selectedUnit || selectedItem?.unit_id}
            showInvestimentos={showCapexSection}
            showEquipe={showPersonnelSection}
            investimentos={
              <CapexMyCostCentersPage
                embedded
                cockpitHero={{
                  title: titleLabel,
                  locationLabel,
                  cycleYear: exerciseYearLabel(context),
                }}
              />
            }
            equipe={<PersonnelBudgetPage embedded hideSectionChrome />}
          />
        ) : null}
        {!bootLoading &&
        modulesUnlocked &&
        selectedCc &&
        !showCapexSection &&
        !showPersonnelSection ? (
          <StateBox variant="warning" dismissible={false}>
            Você não tem vínculo ativo para elaborar o orçamento neste centro. Fale com a
            administração.
          </StateBox>
        ) : null}
      </PageShell>
    );
  }

  return (
    <PageShell title="Meus centros de custo" backRoute="home">
      {bootLoading ? (
        <LoadingActivityCard title="Carregando seus centros…" variant="panel" />
      ) : null}
      {error ? (
        <StateBox variant="error" dismissible={false}>
          {error}
        </StateBox>
      ) : null}
      {!bootLoading && !error && !context?.exercise ? (
        <StateBox variant="warning" dismissible={false}>
          Não há ciclo orçamentário ativo no momento.
        </StateBox>
      ) : null}
      {!bootLoading && !error && context?.exercise && !modulesUnlocked ? (
        <StateBox variant="warning" dismissible={false}>
          Confirme a leitura das orientações para liberar a elaboração.{" "}
          <a href={routeHref("orientacoes")}>Ir para Orientações</a>
        </StateBox>
      ) : null}

      {!bootLoading && !error && modulesUnlocked ? (
        <section className="po-centros" aria-label="Centros de custo disponíveis">
          <header className="po-centros__hero">
            <div className="po-centros__hero-copy">
              <p className="po-centros__eyebrow">Elaboração · {exerciseYearLabel(context)}</p>
              <h2 className="po-centros__title">Seus centros</h2>
              <p className="po-centros__lead">
                Cada card é um centro em que você é responsável. Abra para montar o orçamento
                do ciclo <strong>{exerciseNameLabel(context)}</strong>.
              </p>
            </div>
            <aside className="po-centros__hero-panel" aria-label="Resumo">
              <dl className="po-centros__meta">
                <div>
                  <dt>Disponíveis</dt>
                  <dd>{portfolio.length}</dd>
                </div>
                <div>
                  <dt>Ciclo</dt>
                  <dd>{exerciseYearLabel(context)}</dd>
                </div>
              </dl>
            </aside>
          </header>

          {portfolio.length === 0 ? (
            <div className="po-centros__empty">
              <Building2 size={28} strokeWidth={1.6} aria-hidden="true" />
              <h3>Nenhum centro atribuído</h3>
              <p>
                Quando a administração vincular você a um centro de custo, ele aparecerá
                aqui para elaboração.
              </p>
            </div>
          ) : (
            <>
              <div className="po-centros__toolbar">
                <label className="po-centros__search">
                  <Search size={16} aria-hidden="true" />
                  <span className="po-sr-only">Buscar centro</span>
                  <input
                    type="search"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Buscar por nome, filial ou área…"
                    autoComplete="off"
                  />
                </label>
                <p className="po-centros__count">
                  {filteredPortfolio.length === portfolio.length
                    ? `${portfolio.length} centro${portfolio.length === 1 ? "" : "s"}`
                    : `${filteredPortfolio.length} de ${portfolio.length}`}
                </p>
              </div>

              {filteredPortfolio.length === 0 ? (
                <StateBox variant="default" dismissible={false}>
                  Nenhum centro corresponde à busca.
                </StateBox>
              ) : (
                <ul className="po-centros__grid">
                  {filteredPortfolio.map((row, index) => {
                    const Icon = resolveCostCenterIcon(row.icon_key);
                    const href = centrosHref({
                      costCenterId: row.cost_center_id,
                      unitId: row.unit_id,
                    });
                    const title = cardTitle(row);
                    return (
                      <li
                        key={row.key}
                        className="po-centros__item"
                        style={{ animationDelay: `${Math.min(index, 12) * 35}ms` }}
                      >
                        <a className="po-centros__card" href={href} title={title}>
                          <span className="po-centros__card-icon" aria-hidden="true">
                            <Icon size={26} strokeWidth={1.65} />
                          </span>
                          <span className="po-centros__card-body">
                            <span className="po-centros__card-code">{title}</span>
                            <span className="po-centros__card-branch">
                              <MapPin size={13} aria-hidden="true" />
                              {cardLocation(row)}
                            </span>
                            {row.area_id ? (
                              <span className="po-centros__card-area">Área {row.area_id}</span>
                            ) : null}
                          </span>
                          <span className="po-centros__card-cta">
                            Abrir
                            <ArrowRight size={16} aria-hidden="true" />
                          </span>
                        </a>
                      </li>
                    );
                  })}
                </ul>
              )}
            </>
          )}
        </section>
      ) : null}
    </PageShell>
  );
}
