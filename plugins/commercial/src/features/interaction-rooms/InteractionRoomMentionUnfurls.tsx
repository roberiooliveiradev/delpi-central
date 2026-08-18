import { useEffect, useState } from "react";

import {
  previewInteractionEntity,
  type InteractionMentionDto,
} from "../../api/interactionRoomsApi";
import { navigatePluginPath } from "../../app/pluginNavigation";
import { CommercialEntityUnfurlCard } from "../../app/commercialUi";
import {
  mapPreviewToUnfurlCardModel,
  shouldUnfurlMentionKind,
  type EntityUnfurlCardModel,
} from "./entityUnfurlAdapter";
import { resolveInteractionEntityHref } from "./resolveInteractionEntityHref";

type Props = {
  basePath: string;
  mentions: readonly InteractionMentionDto[];
};

type LoadedCard = {
  key: string;
  model: EntityUnfurlCardModel;
  href: string | null;
};

/**
 * Carrega entity-preview e renderiza EntityUnfurlCard (ok / sem acesso).
 */
export function InteractionRoomMentionUnfurls({ basePath, mentions }: Props) {
  const [cards, setCards] = useState<LoadedCard[]>([]);

  useEffect(() => {
    const targets = mentions.filter((mention) =>
      shouldUnfurlMentionKind(mention.mention_kind),
    );
    if (targets.length === 0) {
      setCards([]);
      return;
    }
    const controller = new AbortController();
    void (async () => {
      const next: LoadedCard[] = [];
      for (const [index, mention] of targets.entries()) {
        try {
          const preview = await previewInteractionEntity(
            mention.mention_kind,
            mention.ref ?? {},
            controller.signal,
          );
          if (controller.signal.aborted) return;
          const model = mapPreviewToUnfurlCardModel(preview);
          next.push({
            key: `${mention.mention_kind}-${index}-${mention.label}`,
            model,
            href: resolveInteractionEntityHref(
              basePath,
              model.hrefStrategy,
              model.ref,
            ),
          });
        } catch {
          if (controller.signal.aborted) return;
          next.push({
            key: `${mention.mention_kind}-${index}-error`,
            model: mapPreviewToUnfurlCardModel({
              kind: mention.mention_kind,
              accessible: false,
              label: mention.label,
              ref: mention.ref ?? {},
            }),
            href: null,
          });
        }
      }
      if (!controller.signal.aborted) setCards(next);
    })();
    return () => controller.abort();
  }, [basePath, mentions]);

  if (cards.length === 0) return null;

  return (
    <>
      {cards.map((card) => (
        <CommercialEntityUnfurlCard
          key={card.key}
          title={card.model.title}
          kindLabel={card.model.kindLabel}
          accessible={card.model.accessible}
          deniedLabel={card.model.deniedLabel}
          fields={card.model.fields}
          openLabel={
            card.model.accessible && card.href ? card.model.openLabel : undefined
          }
          onOpen={
            card.model.accessible && card.href
              ? () => navigatePluginPath(card.href as string)
              : undefined
          }
        />
      ))}
    </>
  );
}
