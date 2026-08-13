import { useEffect, useState } from "react";

import {
  getUserProfile,
  userProfilePhotoAbsoluteUrl,
} from "../../api/userProfileApi";
import { httpGetBlob } from "../../api/httpClient";
import { CommercialAvatar } from "../../app/commercialUi";

type TaskUserChipAvatarProps = {
  userId: string;
  name: string;
};

/**
 * Avatar no chip da tarefa — só visual (sem lightbox).
 * Clique no badge pai abre o perfil; expandir foto fica na página do perfil.
 */
export function TaskUserChipAvatar({ userId, name }: TaskUserChipAvatarProps) {
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
