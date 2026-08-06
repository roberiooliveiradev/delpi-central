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
  EmptyState,
  NavigationCard,
  SectionCard,
  StatusBadge,
} from "@delpi/plugin-ui/index";

import { CM_HELP } from "../../content/helpTooltips";
import { getOpenOrders } from "../../api/openOrdersApi";
import { getMyWorklist } from "../../api/worklistApi";
import { navigatePluginView } from "../../app/pluginNavigation";
import { HomeNavIcon } from "../../app/PluginShell";
import {
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

export function HomePage({ basePath, showAdmin, showWorklist }: HomePageProps) {
  const { sellerIdFilter, myPortfolio } = usePortfolioScope();
  const [ordersLoading, setOrdersLoading] = useState(true);
  const [worklistLoading, setWorklistLoading] = useState(showWorklist);
  const [ordersError, setOrdersError] = useState<string | null>(null);
  const [worklistError, setWorklistError] = useState<string | null>(null);
  const [summary, setSummary] = useState<HomeOrdersKpis>(emptyKpis);
  const [worklistOpen, setWorklistOpen] = useState(0);
  const [worklistOverdue, setWorklistOverdue] = useState(0);
  const [worklistToday, setWorklistToday] = useState(0);

  const reload = useCallback(() => {
    const controller = new AbortController();
    setOrdersLoading(true);
    setOrdersError(null);
    setWorklistLoading(showWorklist);
    setWorklistError(null);

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

    void Promise.allSettled([ordersPromise, worklistPromise]);
    return () => controller.abort();
  }, [sellerIdFilter, showWorklist]);

  useEffect(() => {
    const abort = reload();
    return abort;
  }, [reload]);

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
          subtitle="KPIs de equipe e ROL entram na próxima etapa (P1)."
          hint={CM_HELP.home.management}
          classNames={cmSectionCardClassNames}
          labels={cmSectionLabels}
        >
          <p className="cm-muted">
            Enquanto isso, use o Dashboard Comercial para analytics pesado ou Carteiras para
            administração.
          </p>
          <div className="cm-nav-row">
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
