import { ClipboardList, Settings, Users } from "lucide-react";
import { ActionButton, NavigationCard, SectionCard } from "@delpi/plugin-ui/index";

import { navigatePluginView } from "../../app/pluginNavigation";
import { HomeNavIcon } from "../../app/PluginShell";
import {
  cmNavCardClassNames,
  cmSectionCardClassNames,
  cmSectionLabels,
} from "../../app/commercialUi";

type HomePageProps = {
  basePath: string;
  showAdmin: boolean;
};

const cards = [
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
];

export function HomePage({ basePath, showAdmin }: HomePageProps) {
  const visibleCards = cards.filter((card) => !card.adminOnly || showAdmin);

  return (
    <section className="cm-page-stack">
      <SectionCard
        title="Bem-vindo ao Portal Comercial"
        subtitle="Escolha uma área para continuar. Deep links de clientes usam código + loja."
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <div className="cm-home-grid">
          {visibleCards.map((card) => (
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
      </SectionCard>

      <SectionCard
        title="Atalhos rápidos"
        classNames={cmSectionCardClassNames}
        labels={cmSectionLabels}
      >
        <div className="cm-nav-row">
          <ActionButton variant="ghost" onClick={() => navigatePluginView("open_orders", { basePath })}>
            <ClipboardList size={16} aria-hidden="true" /> Pedidos
          </ActionButton>
          <ActionButton variant="ghost" onClick={() => navigatePluginView("customers", { basePath })}>
            <Users size={16} aria-hidden="true" /> Carteira
          </ActionButton>
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
