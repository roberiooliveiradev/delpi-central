import {
  CommercialEmptyState,
  CommercialPageHero,
  CommercialPagePath,
} from "../../app/commercialUi";
import { buildPluginPath } from "../../app/pluginRoutes";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";

type Props = {
  basePath: string;
};

/** Shell da inbox — lista real na E7.S4. */
export function InteractionRoomsInboxPage({ basePath }: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  return (
    <section className="cm-page-stack">
      <CommercialPagePath
        back={{
          label: "Início",
          href: buildPluginPath("home", basePath),
        }}
        current={content.inboxTitle}
      />
      <CommercialPageHero
        title={content.inboxTitle}
        description={content.inboxSubtitle}
      />
      <CommercialEmptyState
        title={content.inboxEmptyTitle}
        message={content.inboxEmptyDescription}
      />
    </section>
  );
}
