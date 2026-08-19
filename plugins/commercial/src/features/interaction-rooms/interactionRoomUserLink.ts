import type { MouseEventHandler } from "react";

import {
  buildUserProfileHref,
  navigatePluginPath,
} from "../../app/pluginNavigation";
import { profileLinkTitle } from "../../content/entityLinkHints";

export type InteractionRoomUserLink = {
  href: string;
  title: string;
  onNavigate: MouseEventHandler<HTMLAnchorElement>;
};

/** Contrato de avatar/link de usuário — mesmo `buildUserProfileHref` do resto do MFE. */
export function interactionRoomUserLink(
  userId: string | null | undefined,
  name: string,
  basePath: string,
): InteractionRoomUserLink | null {
  const id = (userId ?? "").trim();
  if (!id) return null;
  const href = buildUserProfileHref(id, { basePath });
  if (!href) return null;
  const title = profileLinkTitle(name);
  return {
    href,
    title,
    onNavigate: (event) => {
      event.preventDefault();
      event.stopPropagation();
      navigatePluginPath(href);
    },
  };
}

export function interactionRoomParticipantAvatar(
  userId: string,
  name: string,
  basePath: string,
): {
  id: string;
  name: string;
  href?: string;
  title?: string;
  onNavigate?: InteractionRoomUserLink["onNavigate"];
} {
  const link = interactionRoomUserLink(userId, name, basePath);
  if (!link) return { id: userId, name };
  return {
    id: userId,
    name,
    href: link.href,
    title: link.title,
    onNavigate: link.onNavigate,
  };
}

export function interactionRoomAuthorAvatarFields(
  userId: string | null | undefined,
  name: string,
  basePath: string,
): {
  authorHref?: string;
  authorLinkTitle?: string;
  onAuthorNavigate?: InteractionRoomUserLink["onNavigate"];
} {
  const link = interactionRoomUserLink(userId, name, basePath);
  if (!link) return {};
  return {
    authorHref: link.href,
    authorLinkTitle: link.title,
    onAuthorNavigate: link.onNavigate,
  };
}
