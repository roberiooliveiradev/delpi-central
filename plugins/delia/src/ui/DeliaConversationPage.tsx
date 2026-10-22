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
  /** Prompt 5: context-region content bound to the selected message —
   *  falls back to the empty render-only panel shell. */
  context?: ReactNode;
};

export function DeliaConversationPage({ conversation, context }: DeliaConversationPageProps) {
  const [category, setCategory] = useState<NavigationRailCategory>("conversations");
  const title = category === "projects" ? "Projetos" : category === "agents" ? "Agentes" : category === "plugins" ? "Plugins" : "Conversas";
  return (
    <ConversationThreeRegionLayout
      leftTitle={title}
      rail={<NavigationRail
        activeCategory={category}
        availableCategories={["conversations", "projects", "agents", "plugins"]}
        onSelectCategory={setCategory}
      />}
      left={<NavigationCategoryPanel category={category}>
        {category === "projects" ? <ProjectNavigation status="contract_unavailable" />
          : category === "agents" ? <AgentNavigation status="catalog_unavailable" />
          : category === "plugins" ? <PluginNavigation status="contract_unavailable" />
          : <ConversationNavigation />}
      </NavigationCategoryPanel>}
      right={context ?? <ConversationContextPanel />}
      center={conversation}
    />
  );
}
