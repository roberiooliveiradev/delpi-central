import { useCallback, useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  CalendarCheck,
  ClipboardList,
  ExternalLink,
  Package,
  PackageCheck,
  Settings,
  Users,
  Wallet,
} from "lucide-react";
import {
  ActionButton,
  DataTable,
  EmptyState,
  NavigationCard,
  SectionCard,
  StatusBadge,
  type DataTableColumn,
} from "@delpi/plugin-ui/index";

import { CM_HELP } from "../../content/helpTooltips";
import { getOpenOrders } from "../../api/openOrdersApi";
import { getMyWorklist } from "../../api/worklistApi";
import {
  formatPct,
  getClosingRate,
  getHeadOfficeRolTargetPct,
  getSalesOrderOtd,
  pickClosingPct,
  pickOtdPct,
  pickRolPct,
} from "../../api/commercialKpisApi";
import { navigatePluginView } from "../../app/pluginNavigation";
import { HomeNavIcon } from "../../app/PluginShell";
import {
  cmDataTableClassNames,
  cmDataTableLabels,
  cmEmptyStateClassNames,
  cmNavCardClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
  cmStatusBadgeClassNames,
  CommercialAlertQueue,
  CommercialLoadingCard,
} from "../../app/commercialUi";
import { usePortfolioScope } from "../../app/usePortfolioScope";
import { KpiCard } from "../../components/KpiCard";
import { formatCurrency } from "../../utils/format";
import type { OpenOrdersData } from "../../types/openOrders";
import type { SellerPortfolio } from "../../types/portfolio";

type HomePageProps = {
  basePath: string;
  showAdmin: boolean;
  showWorklist: boolean;
};

type HomeOrdersKpis = {
  totalLinhas: number;
  valorAberto: number;
  podeFaturar: number;
  atrasos: number;
};

function greetingForNow(date = new Date()): string {
  const hour = date.getHours();
  if (hour < 12) return "Bom dia";
  if (hour < 18) return "Boa tarde";
  return "Boa noite";
}

function kpisFromOpenOrders(data: OpenOrdersData): HomeOrdersKpis {
  const items = data.items ?? [];
  const summary = data.summary as
    | (OpenOrdersData["summary"] & {
        itens_com_estoque?: number;
        linhas_em_atraso?: number;
      })
    | undefined;
  const lateFromItems = items.filter((item) => {
    const status = `${item.status ?? ""} ${item.tipo_pedido ?? ""}`.toLowerCase();
    return status.includes("atras");
  }).length;
  return {
    totalLinhas: summary?.total_linhas ?? items.length,
    valorAberto: summary?.valor_total_aberto ?? 0,
    podeFaturar: summary?.itens_com_estoque ?? 0,
    atrasos: summary?.linhas_em_atraso ?? lateFromItems,
  };
}

const emptyKpis: HomeOrdersKpis = {
  totalLinhas: 0,
  valorAberto: 0,
  podeFaturar: 0,
  atrasos: 0,
};

type TeamRow = {
  id: string;
  name: string;
  customers: number;
  lines: number;
  openValue: number;
  error?: string | null;
};

type MgmtKpis = {
  rolPct: number | null;
  closingPct: number | null;
  otdPct: number | null;
};

const emptyMgmt: MgmtKpis = { rolPct: null, closingPct: null, otdPct: null };
const TEAM_FETCH_CAP = 12;

export function HomePage({ basePath, showAdmin, showWorklist }: HomePageProps) {
  const { sellerIdFilter, myPortfolio, sellers } = usePortfolioScope();
  const [ordersLoading, setOrdersLoading] = useState(true);
  const [worklistLoading, setWorklistLoading] = useState(showWorklist);
  const [ordersError, setOrdersError] = useState<string | null>(null);
  const [worklistError, setWorklistError] = useState<string | null>(null);
  const [summary, setSummary] = useState<HomeOrdersKpis>(emptyKpis);
  const [worklistOpen, setWorklistOpen] = useState(0);
  const [worklistOverdue, setWorklistOverdue] = useState(0);
  const [worklistToday, setWorklistToday] = useState(0);
  const [mgmtLoading, setMgmtLoading] = useState(showAdmin);
  const [mgmtError, setMgmtError] = useState<string | null>(null);
  const [mgmtKpis, setMgmtKpis] = useState<MgmtKpis>(emptyMgmt);
  const [teamLoading, setTeamLoading] = useState(showAdmin);
  const [teamRows, setTeamRows] = useState<TeamRow[]>([]);
  const [teamError, setTeamError] = useState<string | null>(null);

  const reload = useCallback(() => {
    const controller = new AbortController();
    setOrdersLoading(true);
    setOrdersError(null);
    setWorklistLoading(showWorklist);
    setWorklistError(null);
    if (showAdmin) {
      setMgmtLoading(true);
      setMgmtError(null);
      setTeamLoading(true);
      setTeamError(null);
    }

    const ordersPromise = getOpenOrders(controller.signal, {
      sellerId: sellerIdFilter,
    })
      .then((data) => {
        setSummary(kpisFromOpenOrders(data));
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setOrdersError(err instanceof Error ? err.message : "Erro ao carregar pedidos.");
        setSummary(emptyKpis);
      })
      .finally(() => {
        if (!controller.signal.aborted) setOrdersLoading(false);
      });

    const worklistPromise = showWorklist
      ? getMyWorklist(controller.signal)
          .then((wl) => {
            setWorklistOpen(wl.counts?.open ?? 0);
            setWorklistOverdue(wl.counts?.overdue ?? 0);
            setWorklistToday(wl.counts?.today ?? 0);
          })
          .catch((err: unknown) => {
            if (controller.signal.aborted) return;
            setWorklistError(err instanceof Error ? err.message : "Erro ao carregar Meu dia.");
            setWorklistOpen(0);
            setWorklistOverdue(0);
            setWorklistToday(0);
          })
          .finally(() => {
            if (!controller.signal.aborted) setWorklistLoading(false);
          })
      : Promise.resolve().then(() => {
          setWorklistLoading(false);
        });

    const mgmtPromise = showAdmin
      ? Promise.allSettled([
          getHeadOfficeRolTargetPct(controller.signal),
          getClosingRate(controller.signal),
          getSalesOrderOtd(controller.signal),
        ])
          .then((results) => {
            if (controller.signal.aborted) return;
            const [rolR, closingR, otdR] = results;
            const next: MgmtKpis = { ...emptyMgmt };
            let failed = 0;
            if (rolR.status === "fulfilled") next.rolPct = pickRolPct(rolR.value);
            else failed += 1;
            if (closingR.status === "fulfilled") next.closingPct = pickClosingPct(closingR.value);
            else failed += 1;
            if (otdR.status === "fulfilled") next.otdPct = pickOtdPct(otdR.value);
            else failed += 1;
            setMgmtKpis(next);
            if (failed === 3) {
              setMgmtError("KPIs de gestão indisponíveis (permissão ou API).");
            } else if (failed > 0) {
              setMgmtError("Alguns KPIs de gestão falharam — os disponíveis seguem abaixo.");
            } else {
              setMgmtError(null);
            }
          })
          .finally(() => {
            if (!controller.signal.aborted) setMgmtLoading(false);
          })
      : Promise.resolve().then(() => {
          setMgmtLoading(false);
        });

    const teamPromise = showAdmin
      ? (async () => {
          const active = sellers.filter((s) => s.active).slice(0, TEAM_FETCH_CAP);
          if (!active.length) {
            setTeamRows([]);
            setTeamError(null);
            return;
          }
          const settled = await Promise.allSettled(
            active.map(async (seller: SellerPortfolio) => {
              const data = await getOpenOrders(controller.signal, {
                sellerId: seller.user_id,
              });
              const kpis = kpisFromOpenOrders(data);
              return {
                id: seller.id,
                name: seller.display_name || seller.user_id,
                customers: seller.customer_count ?? seller.customers?.length ?? 0,
                lines: kpis.totalLinhas,
                openValue: kpis.valorAberto,
                error: null as string | null,
              } satisfies TeamRow;
            }),
          );
          if (controller.signal.aborted) return;
          const rows: TeamRow[] = settled.map((result, index) => {
            const seller = active[index];
            if (result.status === "fulfilled") return result.value;
            return {
              id: seller.id,
              name: seller.display_name || seller.user_id,
              customers: seller.customer_count ?? seller.customers?.length ?? 0,
              lines: 0,
              openValue: 0,
              error: result.reason instanceof Error ? result.reason.message : "Falha",
            };
          });
          setTeamRows(rows);
          if (settled.every((r) => r.status === "rejected")) {
            setTeamError("Não foi possível carregar a tabela da equipe.");
          } else {
            setTeamError(null);
          }
        })()
          .catch((err: unknown) => {
            if (controller.signal.aborted) return;
            setTeamRows([]);
            setTeamError(err instanceof Error ? err.message : "Erro na tabela da equipe.");
          })
          .finally(() => {
            if (!controller.signal.aborted) setTeamLoading(false);
          })
      : Promise.resolve().then(() => {
          setTeamLoading(false);
        });

    void Promise.allSettled([ordersPromise, worklistPromise, mgmtPromise, teamPromise]);
    return () => controller.abort();
  }, [sellerIdFilter, sellers, showAdmin, showWorklist]);

  useEffect(() => {
    const abort = reload();
    return abort;
  }, [reload]);

  const teamColumns = useMemo<DataTableColumn<TeamRow>[]>(
    () => [
      { key: "name", header: "Vendedor", render: (row) => row.name },
      {
        key: "customers",
        header: "Clientes",
        align: "right",
        render: (row) => row.customers.toLocaleString("pt-BR"),
      },
      {
        key: "lines",
        header: "Linhas abertas",
        align: "right",
        render: (row) => (row.error ? "—" : row.lines.toLocaleString("pt-BR")),
      },
      {
        key: "openValue",
        header: "Valor aberto",
        align: "right",
        render: (row) => (row.error ? row.error : formatCurrency(row.openValue)),
      },
    ],
    [],
  );

  const alerts = useMemo(() => {
    const items = [];
    if (summary.atrasos > 0) {
      items.push({
        id: "late-orders",
        title: `${summary.atrasos} linha(s) em atraso`,
        description: "Revise pedidos em aberto e priorize entregas vencidas.",
        tone: "warning" as const,
        actionLabel: "Ver pedidos",
        onAction: () => navigatePluginView("open_orders", { basePath }),
      });
    }
    if (showWorklist && worklistOverdue > 0) {
      items.push({
        id: "overdue-tasks",
        title: `${worklistOverdue} follow-up(s) atrasado(s)`,
        description: "Conclua ou reagende no Meu dia.",
        tone: "danger" as const,
        actionLabel: "Meu dia",
        onAction: () => navigatePluginView("my_day", { basePath }),
      });
    } else if (showWorklist && worklistOpen > 0) {
      items.push({
        id: "open-tasks",
        title: `${worklistOpen} tarefa(s) em aberto`,
        description: "Priorize a fila do Meu dia.",
        tone: "info" as const,
        actionLabel: "Meu dia",
        onAction: () => navigatePluginView("my_day", { basePath }),
      });
    } else if (showWorklist) {
      items.push({
        id: "create-follow-up",
        title: "Nenhum follow-up na fila",
        description: "Agende um follow-up com prazo para não perder o cliente.",
        tone: "info" as const,
        actionLabel: "Criar follow-up",
        onAction: () =>
          navigatePluginView("my_day", { basePath, search: "?createTask=1" }),
      });
    }
    if (summary.totalLinhas === 0 && !ordersError && !ordersLoading) {
      items.push({
        id: "no-orders",
        title: "Nenhum pedido em aberto na carteira",
        description: "Abra a carteira para acompanhar clientes.",
        tone: "neutral" as const,
        actionLabel: "Ver carteira",
        onAction: () => navigatePluginView("customers", { basePath }),
      });
    }
    return items;
  }, [
    basePath,
    ordersError,
    ordersLoading,
    showWorklist,
    summary.atrasos,
    summary.totalLinhas,
    worklistOpen,
    worklistOverdue,
  ]);

  const cards = [
    ...(showWorklist
      ? [
          {
            id: "my_day" as const,
            title: "Meu dia",
            description: "Fila de follow-ups e tarefas do dia.",
            icon: "my_day" as const,
          },
        ]
      : []),
    {
      id: "open_orders" as const,
      title: "Pedidos em aberto",
      description: "Consulte pedidos de venda em aberto no TOTVS.",
      icon: "orders" as const,
    },
    {
      id: "customers" as const,
      title: "Minha carteira",
      description: "Veja clientes da sua carteira com dados enriquecidos.",
      icon: "customers" as const,
    },
    {
      id: "seller_portfolios" as const,
      title: "Carteiras de vendedores",
      description: "Administre carteiras, cadastros e transferências.",
      icon: "admin" as const,
      adminOnly: true,
    },
  ].filter((card) => !("adminOnly" in card && card.adminOnly) || showAdmin);

  const portfolioName = myPortfolio?.display_name?.trim() || "Carteira própria";
  const greeting = greetingForNow();

  return (
    <section className="cm-page-stack">
      <SectionCard
        title={`${greeting} · ${portfolioName}`}
        subtitle="Aqui está o que precisa da sua atenção hoje."
        hint={CM_HELP.home.overview}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <div className="cm-home-hero">
          <div className="cm-home-hero__chips" aria-label="Resumo rápido">
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              variant="info"
              label={`Pedidos: ${summary.totalLinhas.toLocaleString("pt-BR")}`}
            />
            {showWorklist ? (
              <StatusBadge
                classNames={cmStatusBadgeClassNames}
                variant={worklistOverdue > 0 ? "danger" : "neutral"}
                label={`Follow-ups: ${worklistOpen.toLocaleString("pt-BR")}`}
              />
            ) : null}
            <StatusBadge
              classNames={cmStatusBadgeClassNames}
              variant={summary.atrasos > 0 ? "warning" : "neutral"}
              label={`Atrasos: ${summary.atrasos.toLocaleString("pt-BR")}`}
            />
          </div>
          <ActionButton variant="ghost" onClick={() => reload()}>
            Atualizar
          </ActionButton>
        </div>
      </SectionCard>

      <SectionCard
        title="Precisa de atenção"
        subtitle="Alertas da carteira e do Meu dia."
        hint={CM_HELP.home.alerts}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {ordersLoading && worklistLoading ? (
          <CommercialLoadingCard title="Carregando alertas…" variant="panel" />
        ) : (
          <>
            {ordersError ? (
              <EmptyState
                classNames={cmEmptyStateClassNames}
                defaultMessage={`Pedidos: ${ordersError}`}
                role="alert"
              />
            ) : null}
            {worklistError ? (
              <EmptyState
                classNames={cmEmptyStateClassNames}
                defaultMessage={`Meu dia: ${worklistError}`}
                role="alert"
              />
            ) : null}
            <CommercialAlertQueue
              items={alerts}
              emptyMessage="Nada precisa de atenção agora. Bom trabalho!"
            />
          </>
        )}
      </SectionCard>

      <SectionCard
        title="Seus números"
        subtitle="Resumo operacional da carteira no escopo atual."
        hint={CM_HELP.home.kpis}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {ordersLoading ? (
          <CommercialLoadingCard title="Carregando indicadores…" variant="panel" />
        ) : ordersError ? (
          <EmptyState
            classNames={cmEmptyStateClassNames}
            defaultMessage="Indicadores indisponíveis neste momento."
            role="alert"
          />
        ) : (
          <div className="cm-home-kpi-grid" aria-label="Indicadores operacionais">
            <KpiCard
              title="Linhas em aberto"
              titleHint={CM_HELP.openOrders.kpiLines}
              value={summary.totalLinhas.toLocaleString("pt-BR")}
              subtitle="No escopo atual"
              icon={<Package size={22} />}
            />
            <KpiCard
              title="Valor em aberto"
              titleHint={CM_HELP.openOrders.kpiValue}
              value={formatCurrency(summary.valorAberto)}
              icon={<Wallet size={22} />}
              wide
            />
            <KpiCard
              title="Pode faturar"
              titleHint={CM_HELP.openOrders.kpiCanInvoice}
              value={summary.podeFaturar.toLocaleString("pt-BR")}
              icon={<PackageCheck size={22} />}
            />
            <KpiCard
              title="Pedidos em atraso"
              titleHint={CM_HELP.openOrders.kpiLate}
              value={summary.atrasos.toLocaleString("pt-BR")}
              icon={<AlertTriangle size={22} />}
            />
            {showWorklist ? (
              <KpiCard
                title="Tarefas hoje"
                titleHint={CM_HELP.home.kpiTasks}
                value={(worklistToday + worklistOverdue).toLocaleString("pt-BR")}
                subtitle={`${worklistOverdue} atrasada(s)`}
                icon={<CalendarCheck size={22} />}
              />
            ) : null}
          </div>
        )}
      </SectionCard>

      {showAdmin ? (
        <SectionCard
          title="Gestão"
          subtitle="ROL, conversão e OTD do mês + carteiras da equipe."
          hint={CM_HELP.home.management}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          {mgmtLoading ? (
            <CommercialLoadingCard title="Carregando KPIs de gestão…" variant="panel" />
          ) : null}
          {mgmtError ? (
            <EmptyState
              classNames={cmEmptyStateClassNames}
              defaultMessage={mgmtError}
              role="alert"
            />
          ) : null}
          {!mgmtLoading ? (
            <div className="cm-home-kpi-grid" aria-label="Indicadores de gestão">
              <KpiCard
                title="ROL vs meta"
                titleHint={CM_HELP.home.kpiRol}
                value={formatPct(mgmtKpis.rolPct)}
                subtitle="Matriz no mês"
                icon={<Wallet size={22} />}
              />
              <KpiCard
                title="Conversão"
                titleHint={CM_HELP.home.kpiClosing}
                value={formatPct(mgmtKpis.closingPct)}
                subtitle="Propostas → ganhas"
                icon={<PackageCheck size={22} />}
              />
              <KpiCard
                title="OTD pedidos"
                titleHint={CM_HELP.home.kpiOtd}
                value={formatPct(mgmtKpis.otdPct)}
                subtitle="Entrega no prazo"
                icon={<Package size={22} />}
              />
            </div>
          ) : null}

          <h3 className="cm-section-subtitle" style={{ marginTop: 16 }}>
            Equipe (carteiras)
          </h3>
          {teamLoading ? (
            <CommercialLoadingCard title="Carregando equipe…" variant="panel" />
          ) : null}
          {teamError ? (
            <EmptyState
              classNames={cmEmptyStateClassNames}
              defaultMessage={teamError}
              role="alert"
            />
          ) : null}
          {!teamLoading && !teamError && teamRows.length === 0 ? (
            <EmptyState
              classNames={{ ...cmEmptyStateClassNames, withTitle: true }}
              defaultTitle="Nenhuma carteira ativa"
              defaultMessage="Cadastre vendedores em Carteiras para ver a tabela da equipe."
            >
              <ActionButton
                variant="primary"
                onClick={() => navigatePluginView("seller_portfolios", { basePath })}
              >
                Abrir Carteiras
              </ActionButton>
            </EmptyState>
          ) : null}
          {!teamLoading && teamRows.length > 0 ? (
            <DataTable
              rows={teamRows}
              columns={teamColumns}
              rowKey={(row) => row.id}
              classNames={cmDataTableClassNames}
              labels={cmDataTableLabels}
              layout="section"
            />
          ) : null}

          <div className="cm-nav-row" style={{ marginTop: 12 }}>
            <ActionButton
              variant="ghost"
              onClick={() => window.location.assign("/apps/dashboard-commercial")}
            >
              <ExternalLink size={16} aria-hidden="true" /> Dashboard Comercial
            </ActionButton>
            <ActionButton
              variant="primary"
              onClick={() => navigatePluginView("seller_portfolios", { basePath })}
            >
              Abrir Carteiras
            </ActionButton>
          </div>
        </SectionCard>
      ) : null}

      <SectionCard
        title="Atalhos"
        subtitle="Menos de dois cliques até a ação."
        hint={CM_HELP.home.shortcuts}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <div className="cm-home-grid">
          {cards.map((card) => (
            <NavigationCard
              key={card.id}
              classNames={cmNavCardClassNames}
              title={card.title}
              description={card.description}
              icon={<HomeNavIcon target={card.icon} />}
              onClick={() => navigatePluginView(card.id, { basePath })}
            />
          ))}
        </div>
        {!cards.length ? (
          <EmptyState
            classNames={cmEmptyStateClassNames}
            defaultMessage="Nenhuma área disponível para o seu perfil."
          />
        ) : null}
      </SectionCard>

      <SectionCard
        title="Analytics e propostas"
        subtitle="Deep links — BI permanece fora do portal operacional."
        hint={CM_HELP.home.analytics}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <div className="cm-nav-row">
          <ActionButton
            variant="ghost"
            onClick={() => {
              window.location.assign("/apps/dashboard-commercial");
            }}
          >
            <ExternalLink size={16} aria-hidden="true" /> Dashboard Comercial
          </ActionButton>
          <ActionButton
            variant="ghost"
            onClick={() => {
              window.location.assign("/apps/propostas-comerciais");
            }}
          >
            <ExternalLink size={16} aria-hidden="true" /> Propostas
          </ActionButton>
          <ActionButton variant="ghost" onClick={() => navigatePluginView("open_orders", { basePath })}>
            <ClipboardList size={16} aria-hidden="true" /> Pedidos
          </ActionButton>
          <ActionButton variant="ghost" onClick={() => navigatePluginView("customers", { basePath })}>
            <Users size={16} aria-hidden="true" /> Carteira
          </ActionButton>
          {showWorklist ? (
            <ActionButton variant="ghost" onClick={() => navigatePluginView("my_day", { basePath })}>
              <CalendarCheck size={16} aria-hidden="true" /> Meu dia
            </ActionButton>
          ) : null}
          {showAdmin ? (
            <ActionButton
              variant="ghost"
              onClick={() => navigatePluginView("seller_portfolios", { basePath })}
            >
              <Settings size={16} aria-hidden="true" /> Admin
            </ActionButton>
          ) : null}
        </div>
      </SectionCard>
    </section>
  );
}
