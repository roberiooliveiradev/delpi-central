import type { ReactNode } from "react";
import type { ConversationPanelControls } from "@delpi/plugin-ui/index";
import {
  ConversationContextPanel,
  ConversationNavigation,
  NavigationRail,
  NavigationCategoryPanel,
  ConversationThreeRegionLayout,
} from "@delpi/plugin-ui/index";

/** Unified DÉLIA page: visual navigation and real conversation, with no fake backend. */
export type DeliaConversationPageProps = {
  conversation: ReactNode | ((controls: ConversationPanelControls) => ReactNode);
};

export function DeliaConversationPage({ conversation }: DeliaConversationPageProps) {
  return (
    <ConversationThreeRegionLayout
      left={({ collapsed, onExpand }) => collapsed
        ? <NavigationRail activeCategory="conversations" availableCategories={["conversations"]} onSelectCategory={() => onExpand()} />
        : <NavigationCategoryPanel category="conversations"><ConversationNavigation /></NavigationCategoryPanel>}
      right={<ConversationContextPanel />}
      center={conversation}
    />
  );
}
