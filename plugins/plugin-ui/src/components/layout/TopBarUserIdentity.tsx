import {
  useCallback,
  useRef,
  useState,
  type MouseEventHandler,
  type ReactNode,
} from "react";
import type { LucideIcon } from "lucide-react";

import { delpiUiClass } from "../../utils/delpiUiClass";
import { shouldHandleInlineNavClick } from "../navigation/InlineNavLink";
import { AnchoredPanelPortal } from "../shape/AnchoredPanelPortal";
import { ContextMenuItem } from "../menu/ContextMenuItem";
import { isSafeNavigationHref } from "./PagePath";
import {
  InitialsAvatar,
  initialsAvatarBemClasses,
  type InitialsAvatarClassNames,
} from "./InitialsAvatar";

export type TopBarUserIdentityMenuItem = {
  id: string;
  label: string;
  onSelect: () => void;
  disabled?: boolean;
  icon?: LucideIcon;
};

export type TopBarUserIdentityClassNames = {
  root: string;
  profile: string;
  label: string;
  name: string;
};

export type TopBarUserIdentityProps = {
  displayName: string | null;
  fallbackLabel?: string;
  avatarUrl?: string | null;
  loading?: boolean;
  classNames: TopBarUserIdentityClassNames;
  avatarClassNames: InitialsAvatarClassNames;
  className?: string;
  portalScopeClassName?: string;
  href?: string;
  onNavigate?: MouseEventHandler<HTMLAnchorElement>;
  title?: string;
  ariaLabel?: string;
  avatarHref?: string;
  onAvatarNavigate?: () => void;
  avatarTitle?: string;
  onLabelClick?: () => void;
  labelAriaLabel?: string;
  labelHasPopup?: boolean | "menu";
  labelExpanded?: boolean;
  labelEnd?: ReactNode;
  labelDisabled?: boolean;
  menuItems?: TopBarUserIdentityMenuItem[];
  menuAriaLabel?: string;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
};

export function topBarUserIdentityBemClasses(prefix: string): TopBarUserIdentityClassNames {
  return {
    root: delpiUiClass(`${prefix}-topbar-user`, "delpi-ui-topbar-user"),
    profile: delpiUiClass(`${prefix}-topbar-user__profile`, "delpi-ui-topbar-user__profile"),
    label: delpiUiClass(`${prefix}-topbar-user__label`, "delpi-ui-topbar-user__label"),
    name: delpiUiClass(`${prefix}-topbar-user__name`, "delpi-ui-topbar-user__name"),
  };
}

function requireSafeHref(href: string): string {
  if (!isSafeNavigationHref(href)) {
    throw new Error("TopBarUserIdentity recebeu um href que não é interno ao host.");
  }
  return href.trim();
}

/**
 * Chrome de identidade na TopBar: avatar + nome (+ menu opcional).
 * Não busca usuário, não interpreta JWT, não conhece portais.
 */
export function TopBarUserIdentity({
  displayName,
  fallbackLabel = "Usuário",
  avatarUrl = null,
  loading = false,
  classNames,
  avatarClassNames,
  className,
  portalScopeClassName,
  href,
  onNavigate,
  title,
  ariaLabel,
  avatarHref,
  onAvatarNavigate,
  avatarTitle,
  onLabelClick,
  labelAriaLabel,
  labelHasPopup,
  labelExpanded,
  labelEnd,
  labelDisabled = false,
  menuItems,
  menuAriaLabel = "Menu do usuário",
  open: openProp,
  onOpenChange,
}: TopBarUserIdentityProps) {
  const rootRef = useRef<HTMLDivElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const [uncontrolledOpen, setUncontrolledOpen] = useState(false);
  const controlled = typeof openProp === "boolean";
  const open = controlled ? openProp : uncontrolledOpen;

  const setOpen = useCallback(
    (next: boolean) => {
      if (!controlled) setUncontrolledOpen(next);
      onOpenChange?.(next);
    },
    [controlled, onOpenChange],
  );

  const label = (displayName ?? "").trim() || fallbackLabel;
  const hasMenu = Boolean(menuItems && menuItems.length > 0);
  const chipLink = Boolean(href) && !avatarHref && !onLabelClick && !hasMenu;

  const handleLabelClick = () => {
    if (labelDisabled) return;
    if (onLabelClick) {
      onLabelClick();
      return;
    }
    if (hasMenu) setOpen(!open);
  };

  const avatarNode =
    avatarHref != null ? (
      <InitialsAvatar
        name={label}
        size="sm"
        alt=""
        src={avatarUrl}
        classNames={avatarClassNames}
        href={requireSafeHref(avatarHref)}
        title={avatarTitle ?? label}
        onNavigate={
          onAvatarNavigate
            ? (event) => {
                if (!shouldHandleInlineNavClick(event)) return;
                event.preventDefault();
                onAvatarNavigate();
              }
            : undefined
        }
        portalScopeClassName={portalScopeClassName}
      />
    ) : (
      <InitialsAvatar
        name={label}
        size="sm"
        alt=""
        src={avatarUrl}
        classNames={avatarClassNames}
        previewable={false}
        portalScopeClassName={portalScopeClassName}
      />
    );

  const nameSpan = (
    <span className={`${classNames.name} delpi-ui-topbar-collapse-label`}>{label}</span>
  );

  const rootMods = [
    classNames.root,
    className,
    loading ? "delpi-ui-topbar-user--loading" : null,
    open ? "delpi-ui-topbar-user--open" : null,
    labelDisabled ? "delpi-ui-topbar-user--disabled" : null,
  ]
    .filter(Boolean)
    .join(" ");

  if (chipLink && href) {
    const safeHref = requireSafeHref(href);
    return (
      <a
        className={rootMods}
        href={safeHref}
        title={title ?? label}
        aria-label={ariaLabel ?? label}
        aria-busy={loading || undefined}
        onClick={(event) => {
          if (!shouldHandleInlineNavClick(event)) return;
          if (onNavigate) {
            event.preventDefault();
            onNavigate(event);
          }
        }}
      >
        <span className={classNames.profile}>{avatarNode}</span>
        <span className={classNames.label}>{nameSpan}</span>
      </a>
    );
  }

  const labelInteractive = Boolean(onLabelClick || hasMenu) && !labelDisabled;
  const menuPopup =
    labelHasPopup === true || labelHasPopup === "menu"
      ? "menu"
      : labelHasPopup === false
        ? undefined
        : hasMenu
          ? "menu"
          : undefined;
  const expanded =
    menuPopup === "menu"
      ? typeof labelExpanded === "boolean"
        ? labelExpanded
        : open
      : undefined;

  return (
    <div ref={rootRef} className={rootMods} aria-busy={loading || undefined}>
      <span
        className={[
          classNames.profile,
          avatarHref ? null : "delpi-ui-topbar-user__profile--static",
        ]
          .filter(Boolean)
          .join(" ")}
      >
        {avatarNode}
      </span>

      {labelInteractive ? (
        <button
          ref={triggerRef}
          type="button"
          className={classNames.label}
          aria-label={labelAriaLabel ?? label}
          aria-haspopup={menuPopup}
          aria-expanded={expanded}
          disabled={labelDisabled}
          onClick={handleLabelClick}
        >
          {nameSpan}
          {labelEnd}
        </button>
      ) : (
        <div className={classNames.label} aria-label={labelAriaLabel ?? label}>
          {nameSpan}
          {labelEnd}
        </div>
      )}

      {hasMenu ? (
        <AnchoredPanelPortal
          open={open}
          anchorRef={rootRef}
          panelRef={panelRef}
          className="delpi-ui-context-menu"
          variant="bare"
          role="menu"
          aria-label={menuAriaLabel}
          preferredPlacement="bottom"
          gap={6}
          portalScopeClassName={portalScopeClassName}
          onDismiss={() => {
            setOpen(false);
            triggerRef.current?.focus();
          }}
        >
          {(menuItems ?? []).map((item) => (
            <ContextMenuItem
              key={item.id}
              label={item.label}
              icon={item.icon}
              disabled={item.disabled}
              onSelect={() => {
                item.onSelect();
                setOpen(false);
                triggerRef.current?.focus();
              }}
            />
          ))}
        </AnchoredPanelPortal>
      ) : null}
    </div>
  );
}

export type DashboardTopBarUserIdentityProps = Omit<
  TopBarUserIdentityProps,
  "classNames" | "avatarClassNames"
>;

export function createDashboardTopBarUserIdentity(config: { prefix: string }) {
  const classNames = topBarUserIdentityBemClasses(config.prefix);
  const avatarClassNames = initialsAvatarBemClasses(config.prefix);
  return function DashboardTopBarUserIdentity(props: DashboardTopBarUserIdentityProps) {
    return (
      <TopBarUserIdentity
        classNames={classNames}
        avatarClassNames={avatarClassNames}
        {...props}
      />
    );
  };
}
