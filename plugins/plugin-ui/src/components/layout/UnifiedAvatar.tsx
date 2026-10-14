import {
  useEffect,
  useId,
  useRef,
  useState,
  type MouseEventHandler,
} from "react";
import { Sparkles, UserRound, X } from "lucide-react";

import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { InitialsAvatar, initialsAvatarBemClasses } from "./InitialsAvatar";
import { isSafeNavigationHref } from "./PagePath";

export type AvatarSize = "xs" | "sm" | "md" | "lg" | "xl";
export type AssistantMotionState =
  | "idle"
  | "receiving"
  | "processing"
  | "responding"
  | "attention"
  | "disabled";

/**
 * Presentation-only projection. These fields must come from an
 * authorized owner-published contract; the kit never fetches them.
 */
export type PublishedAvatarProfile = {
  displayName: string;
  jobTitle?: string | null;
  department?: string | null;
  unit?: string | null;
  profileHref?: string | null;
  onNavigate?: MouseEventHandler<HTMLAnchorElement>;
};

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
      /** Optional contract-ready UI; not populated by DELIA yet. */
      profile?: PublishedAvatarProfile | null;
    });

const initialsClasses = initialsAvatarBemClasses("unified");
const HOVER_OPEN_DELAY_MS = 200;
const HOVER_CLOSE_DELAY_MS = 240;

/** Defense in depth. Origin approval remains with the publishing owner. */
export function isSafeAvatarImageUrl(value: string): boolean {
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

function publishedProfileHref(href: string | null | undefined): string | null {
  const value = href?.trim() ?? "";
  return value && isSafeNavigationHref(value) ? value : null;
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
  profile,
}: Extract<UnifiedAvatarProps, { kind: "person" }>) {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const closeRef = useRef<HTMLButtonElement>(null);
  const hoverTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const focusOnOpenRef = useRef(false);
  const popoverId = useId();

  const publishedName = profile?.displayName.trim() ?? "";
  const jobTitle = profile?.jobTitle?.trim() || null;
  const department = profile?.department?.trim() || null;
  const unit = profile?.unit?.trim() || null;
  const href = publishedProfileHref(profile?.profileHref);
  const canShowProfile = Boolean(
    publishedName && (jobTitle || department || unit || href),
  );
  const initialsName = fallbackText?.trim() || null;
  const imageCandidate = imageUrl?.trim() ?? "";
  const safeImageUrl = isSafeAvatarImageUrl(imageCandidate) ? imageCandidate : null;

  const cancelHover = () => {
    if (hoverTimerRef.current !== null) clearTimeout(hoverTimerRef.current);
    hoverTimerRef.current = null;
  };
  const dismiss = (restoreFocus: boolean) => {
    cancelHover();
    setOpen(false);
    if (restoreFocus) anchorRef.current?.focus();
  };
  const scheduleOpen = () => {
    if (!canShowProfile) return;
    cancelHover();
    focusOnOpenRef.current = false;
    hoverTimerRef.current = setTimeout(() => setOpen(true), HOVER_OPEN_DELAY_MS);
  };
  const scheduleClose = () => {
    cancelHover();
    hoverTimerRef.current = setTimeout(() => setOpen(false), HOVER_CLOSE_DELAY_MS);
  };

  useEffect(() => () => {
    if (hoverTimerRef.current !== null) clearTimeout(hoverTimerRef.current);
  }, []);
  useEffect(() => {
    if (!canShowProfile) setOpen(false);
  }, [canShowProfile]);
  useEffect(() => {
    if (open && focusOnOpenRef.current) closeRef.current?.focus();
  }, [open]);

  const visual = (
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
  );
  const classes = avatarClassName(size, className) + " delpi-ui-unified-avatar--person";

  // No profile data published to DELIA today: accessible static fallback only.
  if (!canShowProfile) {
    return (
      <span className={classes} data-kind="person" role="img" aria-label={label}>
        {visual}
      </span>
    );
  }

  return (
    <>
      <button
        type="button"
        ref={anchorRef}
        className={"delpi-ui-unified-avatar__trigger " + classes}
        data-kind="person"
        aria-label={"Ver perfil de " + publishedName}
        aria-haspopup="dialog"
        aria-controls={open ? popoverId : undefined}
        aria-expanded={open}
        onMouseEnter={scheduleOpen}
        onMouseLeave={scheduleClose}
        onClick={() => {
          cancelHover();
          if (open) dismiss(true);
          else {
            focusOnOpenRef.current = true;
            setOpen(true);
          }
        }}
      >
        {visual}
      </button>
      <AnchoredPanelPortal
        open={open}
        anchorRef={anchorRef}
        panelRef={panelRef}
        variant="bare"
        role="dialog"
        aria-label={"Perfil de " + publishedName}
        className="delpi-ui-unified-avatar__popover"
        gap={8}
        onPanelMouseEnter={cancelHover}
        onPanelMouseLeave={scheduleClose}
        onDismiss={() => dismiss(true)}
      >
        <div id={popoverId} className="delpi-ui-unified-avatar__profile">
          <div className="delpi-ui-unified-avatar__profile-head">
            <strong className="delpi-ui-unified-avatar__profile-name">
              {publishedName}
            </strong>
            <button
              ref={closeRef}
              type="button"
              className="delpi-ui-unified-avatar__close"
              aria-label="Fechar detalhes do perfil"
              onClick={() => dismiss(true)}
            >
              <X size={16} aria-hidden="true" />
            </button>
          </div>
          {jobTitle ? <span className="delpi-ui-unified-avatar__detail">{jobTitle}</span> : null}
          {department ? <span className="delpi-ui-unified-avatar__detail">{department}</span> : null}
          {unit ? <span className="delpi-ui-unified-avatar__detail">{unit}</span> : null}
          {href ? (
            <a
              className="delpi-ui-unified-avatar__profile-link"
              href={href}
              onClick={profile?.onNavigate}
            >
              Abrir meu perfil
            </a>
          ) : null}
        </div>
      </AnchoredPanelPortal>
    </>
  );
}
