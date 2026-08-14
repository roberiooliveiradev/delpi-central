import { useEffect, useState, type MouseEventHandler } from "react";

import {
  getUserProfile,
  userProfilePhotoAbsoluteUrl,
} from "../../api/userProfileApi";
import { httpGetBlob } from "../../api/httpClient";
import { CommercialAvatar } from "../../app/commercialUi";

type TaskUserChipAvatarBase = {
  userId: string;
  name: string;
};

export type TaskUserChipAvatarProps = TaskUserChipAvatarBase &
  (
    | {
        href: string;
        title: string;
        onNavigate?: MouseEventHandler<HTMLAnchorElement>;
      }
    | {
        href?: undefined;
        title?: undefined;
        onNavigate?: undefined;
      }
  );

/**
 * Avatar no chip — com href vira link para o perfil; senão só visual.
 */
export function TaskUserChipAvatar(props: TaskUserChipAvatarProps) {
  const { userId, name } = props;
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);

  useEffect(() => {
    const uid = userId.trim();
    if (!uid) {
      setPhotoUrl(null);
      return;
    }
    const controller = new AbortController();
    let created: string | null = null;
    void (async () => {
      try {
        const profile = await getUserProfile(uid, controller.signal);
        if (controller.signal.aborted || !profile.has_photo) {
          if (!controller.signal.aborted) setPhotoUrl(null);
          return;
        }
        const blob = await httpGetBlob(userProfilePhotoAbsoluteUrl(uid), {
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        created = URL.createObjectURL(blob);
        setPhotoUrl(created);
      } catch {
        if (!controller.signal.aborted) setPhotoUrl(null);
      }
    })();
    return () => {
      controller.abort();
      if (created) URL.revokeObjectURL(created);
    };
  }, [userId]);

  if (props.href) {
    return (
      <CommercialAvatar
        name={name}
        colorKey={userId}
        size="sm"
        src={photoUrl}
        href={props.href}
        title={props.title}
        onNavigate={props.onNavigate}
        portalScopeClassName="dashboard-commercial"
      />
    );
  }

  return (
    <CommercialAvatar
      name={name}
      colorKey={userId}
      size="sm"
      src={photoUrl}
      previewable={false}
      portalScopeClassName="dashboard-commercial"
    />
  );
}
