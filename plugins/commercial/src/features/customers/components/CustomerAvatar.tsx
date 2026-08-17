import { useEffect, useState, type MouseEventHandler } from "react";
import { createInitialsAvatar } from "@delpi/plugin-ui/index";

import { fetchCustomerAvatarObjectUrl } from "../../../api/customerEnrichmentApi";

const Avatar = createInitialsAvatar("cm");

type CustomerAvatarBase = {
  code: string;
  store: string;
  name: string;
  hasAvatar?: boolean;
  size?: "sm" | "md" | "lg";
  /** Bump after upload/replace to refetch the blob while hasAvatar stays true. */
  refreshKey?: number;
  previewable?: boolean;
};

export type CustomerAvatarProps = CustomerAvatarBase &
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
 * Avatar do cliente — chrome no kit (`InitialsAvatar`); fetch do blob fica no MFE.
 * Com `href`+`title`, vira link (sem lightbox).
 */
export function CustomerAvatar(props: CustomerAvatarProps) {
  const {
    code,
    store,
    name,
    hasAvatar = false,
    size = "md",
    refreshKey = 0,
    previewable = true,
  } = props;
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
  }, [code, store, hasAvatar, refreshKey]);

  if (props.href) {
    return (
      <Avatar
        name={name || code}
        colorKey={key}
        src={objectUrl}
        size={size}
        href={props.href}
        title={props.title}
        onNavigate={props.onNavigate}
      />
    );
  }

  return (
    <Avatar
      name={name || code}
      colorKey={key}
      src={objectUrl}
      size={size}
      portalScopeClassName="dashboard-commercial"
      previewTitle={previewable ? name || code : undefined}
      previewable={previewable}
    />
  );
}
