import type { ReactNode } from "react";
import {
  ConversationContextPanel,
  ConversationSidebar,
  ConversationThreeRegionLayout,
} from "@delpi/plugin-ui/index";

/** Unified DÉLIA page: visual navigation and real conversation, with no fake backend. */
export type DeliaConversationPageProps = {
  conversation: ReactNode;
};

export function DeliaConversationPage({ conversation }: DeliaConversationPageProps) {
  return (
    <ConversationThreeRegionLayout
      left={<ConversationSidebar />}
      right={<ConversationContextPanel />}
      center={conversation}
    />
  );
}
