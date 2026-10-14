import { useEffect } from "react";
import { Sparkles, UserRound } from "lucide-react";

import { InitialsAvatar, initialsAvatarBemClasses } from "./InitialsAvatar";

export type AvatarSize = "xs" | "sm" | "md" | "lg" | "xl";
export type AssistantMotionState =
  | "idle"
  | "receiving"
  | "processing"
  | "responding"
  | "attention"
  | "disabled";

type AvatarBaseProps = {
  label: string;
  size?: AvatarSize;
  className?: string;
};

export type UnifiedAvatarProps =
  | (AvatarBaseProps & {
      kind: "assistant";
      motionState?: AssistantMotionState;
      /** A real one-shot animation has ended (or reduced motion disables it). */
      onMotionComplete?: () => void;
    })
  | (AvatarBaseProps & {
      kind: "person";
      /** Only an owner-approved, already-published photo URL. */
      imageUrl?: string | null;
      /** Only an owner-published display name, never JWT claims. */
      fallbackText?: string | null;
    });

const initialsClasses = initialsAvatarBemClasses("unified");

/**
 * Syntax/scheme validation only. This does not approve the image origin:
 * owner-published profile contracts remain responsible for origin authorization.
 */
function isSupportedAvatarImageUrl(value: string): boolean {
  const url = value.trim();
  if (!url || /[\u0000-\u001f\\]/.test(url)) return false;
  if (url.startsWith("/") && !url.startsWith("//")) return true;
  if (/^blob:https?:\/\//i.test(url)) return true;
  if (!/^https?:\/\//i.test(url)) return false;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "https:" || parsed.protocol === "http:";
  } catch {
    return false;
  }
}

function avatarClassName(size: AvatarSize, className?: string): string {
  return [
    "delpi-ui-unified-avatar",
    "delpi-ui-unified-avatar--" + size,
    className,
  ].filter(Boolean).join(" ");
}

/** Provider-neutral visual composition. No identity, AuthZ or API ownership. */
export function UnifiedAvatar(props: UnifiedAvatarProps) {
  if (props.kind === "assistant") return <AssistantAvatar {...props} />;
  return <PersonAvatar {...props} />;
}

function AssistantAvatar({
  label,
  size = "md",
  className,
  motionState = "idle",
  onMotionComplete,
}: Extract<UnifiedAvatarProps, { kind: "assistant" }>) {
  // No artificial completion timer. Reduced-motion has no animationend event.
  useEffect(() => {
    if (
      motionState === "responding" &&
      typeof window !== "undefined" &&
      window.matchMedia?.("(prefers-reduced-motion: reduce)").matches
    ) {
      onMotionComplete?.();
    }
  }, [motionState, onMotionComplete]);

  return (
    <span
      className={avatarClassName(size, className) + " delpi-ui-unified-avatar--assistant"}
      data-kind="assistant"
      data-motion={motionState}
      role="img"
      aria-label={label}
    >
      <span
        className="delpi-ui-unified-avatar__visual"
        aria-hidden="true"
        onAnimationEnd={(event) => {
          if (
            event.target === event.currentTarget &&
            motionState === "responding" &&
            event.animationName === "delpi-ui-unified-respond"
          ) {
            onMotionComplete?.();
          }
        }}
      >
        <Sparkles strokeWidth={2.1} />
      </span>
    </span>
  );
}

function PersonAvatar({
  label,
  size = "md",
  className,
  imageUrl,
  fallbackText,
}: Extract<UnifiedAvatarProps, { kind: "person" }>) {
  const initialsName = fallbackText?.trim() || null;
  const imageCandidate = imageUrl?.trim() ?? "";
  const safeImageUrl = isSupportedAvatarImageUrl(imageCandidate) ? imageCandidate : null;
  const classes = avatarClassName(size, className) + " delpi-ui-unified-avatar--person";

  return (
    <span className={classes} data-kind="person" role="img" aria-label={label}>
      <span className="delpi-ui-unified-avatar__visual" aria-hidden="true">
        <InitialsAvatar
          name={initialsName ?? label}
          src={safeImageUrl}
          alt=""
          size="md"
          previewable={false}
          classNames={initialsClasses}
          fallbackNode={initialsName ? undefined : <UserRound strokeWidth={1.8} />}
          style={
            initialsName
              ? undefined
              : { background: "transparent", color: "inherit" }
          }
        />
      </span>
    </span>
  );
}
