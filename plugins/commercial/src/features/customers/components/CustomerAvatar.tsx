import { useEffect, useState } from "react";
import { createInitialsAvatar } from "@delpi/plugin-ui/index";

import { fetchCustomerAvatarObjectUrl } from "../../../api/customerEnrichmentApi";

const Avatar = createInitialsAvatar("pva");

type CustomerAvatarProps = {
  code: string;
  store: string;
  name: string;
  hasAvatar?: boolean;
  size?: "sm" | "md" | "lg";
};

/**
 * Avatar do cliente — chrome no kit (`InitialsAvatar`); fetch do blob fica no MFE.
 */
export function CustomerAvatar({
  code,
  store,
  name,
  hasAvatar = false,
  size = "md",
}: CustomerAvatarProps) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const key = `${code}|${store}`;

  useEffect(() => {
    if (!hasAvatar) {
      setObjectUrl(null);
      return;
    }
    const controller = new AbortController();
    let created: string | null = null;
    void fetchCustomerAvatarObjectUrl(code, store, controller.signal).then((url) => {
      if (controller.signal.aborted) {
        if (url) URL.revokeObjectURL(url);
        return;
      }
      created = url;
      setObjectUrl(url);
    });
    return () => {
      controller.abort();
      if (created) URL.revokeObjectURL(created);
    };
  }, [code, store, hasAvatar]);

  return (
    <Avatar
      name={name || code}
      colorKey={key}
      src={objectUrl}
      size={size}
    />
  );
}
