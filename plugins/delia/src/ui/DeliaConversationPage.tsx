import { useState } from "react";
import type { ReactNode } from "react";
import type { ConversationPanelControls, NavigationRailCategory } from "@delpi/plugin-ui/index";
import {
  ConversationContextPanel,
  ConversationNavigation,
  NavigationRail,
  NavigationCategoryPanel,
  ProjectNavigation,
  AgentNavigation,
  PluginNavigation,
  ConversationThreeRegionLayout,
} from "@delpi/plugin-ui/index";

/** Unified DÉLIA page: persistent category rail and governed, render-only panels. */
export type DeliaConversationPageProps = {
  conversation: ReactNode | ((controls: ConversationPanelControls) => ReactNode);
};

export function DeliaConversationPage({ conversation }: DeliaConversationPageProps) {
  const [category, setCategory] = useState<NavigationRailCategory>("conversations");
  const title = category === "projects" ? "Projetos" : category === "agents" ? "Agentes" : category === "plugins" ? "Plugins" : "Conversas";
  return (
    <ConversationThreeRegionLayout
      leftTitle={title}
      rail={({ onExpand }) => <NavigationRail
        activeCategory={category}
        availableCategories={["conversations", "projects", "agents", "plugins"]}
        onSelectCategory={(nextCategory) => { setCategory(nextCategory); onExpand(); }}
      />}
      left={<NavigationCategoryPanel category={category}>
        {category === "projects" ? <ProjectNavigation status="contract_unavailable" />
          : category === "agents" ? <AgentNavigation status="catalog_unavailable" />
          : category === "plugins" ? <PluginNavigation status="contract_unavailable" />
          : <ConversationNavigation />}
      </NavigationCategoryPanel>}
      right={<ConversationContextPanel />}
      center={conversation}
    />
  );
}
