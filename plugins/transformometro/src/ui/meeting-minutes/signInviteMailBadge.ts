import type { StatusBadgeVariant } from "@delpi/plugin-ui/index";

export type LastInviteMail = {
  send_status?: string | null;
  delivery_status?: string | null;
  send_status_label?: string | null;
  delivery_status_label?: string | null;
  badge_hint?: string | null;
};

export type SignInviteMailBadgeView = {
  label: string;
  variant: StatusBadgeVariant;
  title: string;
};

export function resolveSignInviteMailBadge(
  mail: LastInviteMail | null | undefined,
): SignInviteMailBadgeView | null {
  const sendStatus = String(mail?.send_status || "").trim();
  if (!sendStatus || sendStatus === "pending") {
    return null;
  }

  const deliveryStatus = String(mail?.delivery_status || "").trim();
  let variant: StatusBadgeVariant = "neutral";

  if (sendStatus === "accepted") {
    if (deliveryStatus === "delivered") {
      variant = "success";
    } else if (deliveryStatus === "trace_pending") {
      variant = "warning";
    } else if (deliveryStatus === "bounced") {
      variant = "danger";
    }
  } else if (sendStatus === "failed" || sendStatus === "skipped_no_email") {
    variant = "danger";
  }

  const label =
    sendStatus === "accepted" && mail?.delivery_status_label
      ? String(mail.delivery_status_label)
      : String(mail?.send_status_label || sendStatus);

  const title = String(mail?.badge_hint || "").trim() || label;
  return { label, variant, title };
}
