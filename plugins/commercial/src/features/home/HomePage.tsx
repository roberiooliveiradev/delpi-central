import { useEffect, useMemo, useState } from "react";
import { CalendarCheck, ClipboardList, ExternalLink, Settings, Users } from "lucide-react";
import {
  ActionButton,
  EmptyState,
  NavigationCard,
  SectionCard,
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
  CommercialAlertQueue,
  CommercialLoadingCard,
} from "../../app/commercialUi";
import { usePortfolioScope } from "../../app/usePortfolioScope";

type HomePageProps = {
  basePath: string;
  showAdmin: boolean;
  showWorklist: boolean;
};

export function HomePage({ basePath, showAdmin, showWorklist }: HomePageProps) {
  const { sellerIdFilter, myPortfolio } = usePortfolioScope();
  const [loading, setLoading] = useState(true);
  const [ordersError, setOrdersError] = useState<string | null>(null);
  const [openCount, setOpenCount] = useState(0);
  const [atrasadosHint, setAtrasadosHint] = useState(0);
  const [worklistOpen, setWorklistOpen] = useState(0);
  const [worklistOverdue, setWorklistOverdue] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setOrdersError(null);

    const ordersPromise = getOpenOrders(controller.signal, {
      sellerId: sellerIdFilter,
    })
      .then((data) => {
        const items = data.items ?? [];
        setOpenCount(data.summary?.total_linhas ?? items.length);
        const late = items.filter((item) => {
          const status = `${item.status ?? ""} ${item.tipo_pedido ?? ""}`.toLowerCase();
          return status.includes("atras");
        }).length;
        setAtrasadosHint(late);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setOrdersError(err instanceof Error ? err.message : "Erro ao carregar pedidos.");
        setOpenCount(0);
        setAtrasadosHint(0);
      });

    const worklistPromise = showWorklist
      ? getMyWorklist(controller.signal)
          .then((wl) => {
            setWorklistOpen(wl.counts?.open ?? 0);
            setWorklistOverdue(wl.counts?.overdue ?? 0);
          })
          .catch(() => {
            if (controller.signal.aborted) return;
            setWorklistOpen(0);
            setWorklistOverdue(0);
          })
      : Promise.resolve();

    Promise.allSettled([ordersPromise, worklistPromise]).finally(() => {
      if (!controller.signal.aborted) setLoading(false);
    });

    return () => controller.abort();
  }, [sellerIdFilter, showWorklist]);

  const alerts = useMemo(() => {
    const items = [];
    if (atrasadosHint > 0) {
      items.push({
        id: "late-orders",
        title: `${atrasadosHint} pedido(s) com indício de atraso`,
        description: "Revise a lista de pedidos em aberto.",
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
    if (openCount === 0 && !ordersError && !loading) {
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
    atrasadosHint,
    basePath,
    loading,
    openCount,
    ordersError,
    showWorklist,
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

  return (
    <section className="cm-page-stack">
      <SectionCard
        title={`Olá · ${portfolioName}`}
        subtitle={
          ordersError
            ? `Resumo parcial — ${ordersError}`
            : `Pedidos em aberto: ${openCount}. Atualize para ver alertas da carteira.`
        }
        hint={CM_HELP.home.overview}
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        {loading ? (
          <CommercialLoadingCard title="Carregando visão geral…" variant="panel" />
        ) : (
          <CommercialAlertQueue
            items={alerts}
            emptyMessage="Nada precisa de atenção agora. Bom trabalho!"
          />
        )}
      </SectionCard>

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
