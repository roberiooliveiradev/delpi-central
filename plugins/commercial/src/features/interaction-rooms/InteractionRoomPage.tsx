import {
  CommercialEmptyState,
  CommercialPageHero,
  CommercialPagePath,
} from "../../app/commercialUi";
import {
  buildInteractionRoomsPath,
  buildPluginPath,
} from "../../app/pluginRoutes";
import { INTERACTION_ROOMS_CONTENT } from "../../content/interactionRoomsContent";

type Props = {
  basePath: string;
  roomId: string;
};

/** Shell da sala — thread real na E7.S5. */
export function InteractionRoomPage({ basePath, roomId }: Props) {
  const content = INTERACTION_ROOMS_CONTENT;
  const inboxHref =
    buildInteractionRoomsPath(basePath) ?? buildPluginPath("home", basePath);

  return (
    <section className="cm-page-stack">
      <CommercialPagePath
        back={{
          label: content.inboxTitle,
          href: inboxHref,
        }}
        current={content.roomFallbackTitle}
      />
      <CommercialPageHero
        title={content.roomFallbackTitle}
        description={roomId.trim() || content.roomMissingId}
      />
      <CommercialEmptyState
        title={content.roomEmptyTitle}
        message={content.roomEmptyDescription}
      />
    </section>
  );
}
