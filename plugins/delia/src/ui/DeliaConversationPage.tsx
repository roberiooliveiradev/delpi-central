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
  /** Spec 127: context-region content scoped to the whole conversation —
   *  per-message context lives in each message's own popover. */
  context?: ReactNode;
  /** Controlled open state of the global conversation panel — independent
   *  of any message popover. */
  contextOpen?: boolean;
  onContextOpenChange?: (open: boolean) => void;
};

export function DeliaConversationPage({ conversation, context, contextOpen, onContextOpenChange }: DeliaConversationPageProps) {
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
      rightOpen={contextOpen}
      onRightOpenChange={onContextOpenChange}
      center={conversation}
    />
  );
}
