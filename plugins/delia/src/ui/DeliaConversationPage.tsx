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
  ConversationThreeRegionLayout,
} from "@delpi/plugin-ui/index";

/** Unified DÉLIA page; project category is UI preview, not a project contract. */
export type DeliaConversationPageProps = {
  conversation: ReactNode | ((controls: ConversationPanelControls) => ReactNode);
};

export function DeliaConversationPage({ conversation }: DeliaConversationPageProps) {
  const [category, setCategory] = useState<NavigationRailCategory>("conversations");
  const title = category === "projects" ? "Projetos" : category === "agents" ? "Agentes" : "Conversas";
  return (
    <ConversationThreeRegionLayout
      leftTitle={title}
      left={({ collapsed, onExpand }) => collapsed
        ? <NavigationRail activeCategory={category}
            availableCategories={["conversations", "projects", "agents"]}
            onSelectCategory={(nextCategory) => {
              if (nextCategory !== "conversations" && nextCategory !== "projects" && nextCategory !== "agents") return;
              setCategory(nextCategory);
              onExpand();
            }} />
        : <NavigationCategoryPanel category={category}>
            {category === "projects" ? <ProjectNavigation status="contract_unavailable" /> : category === "agents" ? <AgentNavigation status="catalog_unavailable" /> : <ConversationNavigation />}
          </NavigationCategoryPanel>}
      right={<ConversationContextPanel />}
      center={conversation}
    />
  );
}
