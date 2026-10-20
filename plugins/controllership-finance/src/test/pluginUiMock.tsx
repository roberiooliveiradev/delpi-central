/**
 * Stub Vitest de `@delpi/plugin-ui/index` — mesmo padrão dos MFEs irmãos:
 * renderiza labels/props essenciais sem carregar o barrel (recharts/xyflow).
 */
import { createElement, forwardRef, type ReactNode } from "react";

type AnyProps = Record<string, unknown>;

function el(tag: string, props: AnyProps | null, ...children: ReactNode[]) {
  return createElement(tag, props, ...children);
}

export function ActionButton(props: {
  children?: ReactNode;
  onClick?: () => void;
  variant?: string;
  "aria-label"?: string;
}) {
  return el(
    "button",
    {
      type: "button",
      onClick: props.onClick,
      "aria-label": props["aria-label"],
    },
    props.children,
  );
}

export function EmptyState(props: { defaultMessage?: string }) {
  return el("p", { "data-testid": "empty-state" }, props.defaultMessage);
}

export function PluginErrorBoundary(props: { children?: ReactNode }) {
  return el("div", null, props.children);
}

export function formatPortalGreeting(input: { firstName?: string | null }) {
  return input.firstName ? `Olá, ${input.firstName}` : "Olá";
}

const passthroughClasses = () => ({});

export const catalogSearchBarBemClasses = passthroughClasses;
export const emptyStateCardBemClasses = passthroughClasses;
export const sectionCardPacBemClasses = passthroughClasses;
export const sectionRouteCardBemClasses = passthroughClasses;
export const stateBannerBemClasses = passthroughClasses;
export const statusBadgeBemClasses = passthroughClasses;
export const titleWithHelpBemClasses = passthroughClasses;

export function createDashboardPageHero() {
  return function PageHero(props: {
    eyebrow?: ReactNode;
    title?: ReactNode;
    description?: ReactNode;
    badge?: ReactNode;
    highlights?: Array<{ id: string; label: ReactNode; value: ReactNode }>;
    "aria-label"?: string;
  }) {
    return el(
      "header",
      { "aria-label": props["aria-label"] },
      props.eyebrow,
      el("h1", null, props.title),
      props.description,
      props.badge,
      ...(props.highlights ?? []).map((h) =>
        el("div", { key: h.id }, h.label, h.value),
      ),
    );
  };
}

export function createDashboardStatusBadge() {
  return function StatusBadge(props: { label?: ReactNode }) {
    return el("span", null, props.label);
  };
}

export function createDashboardViewTransition() {
  return function ViewTransition(props: { children?: ReactNode }) {
    return el("div", null, props.children);
  };
}

export function createDashboardTitleWithHelp() {
  return function TitleWithHelp(props: { title?: ReactNode; hint?: string }) {
    return el("span", null, props.title);
  };
}

export function createDashboardStateBanner() {
  return function StateBanner(props: {
    children?: ReactNode;
    variant?: string;
  }) {
    return el("div", { role: "status" }, props.children);
  };
}

export function createDashboardLoadingActivityCard() {
  return function LoadingCard(props: { title?: ReactNode }) {
    return el("p", { role: "status" }, props.title);
  };
}

export function createDashboardSectionCard() {
  return function SectionCard(props: {
    title?: ReactNode;
    subtitle?: ReactNode;
    children?: ReactNode;
  }) {
    return el(
      "section",
      null,
      el("h2", null, props.title),
      props.subtitle,
      props.children,
    );
  };
}

export function createDashboardEventsSection() {
  return function EventsSection(props: {
    title?: ReactNode;
    subtitle?: ReactNode;
    items?: Array<{ id: string }>;
    emptyMessage?: ReactNode;
    listAriaLabel?: string;
  }) {
    const items = props.items ?? [];
    return el(
      "section",
      { "aria-label": props.listAriaLabel },
      el("h2", null, props.title),
      items.length === 0
        ? el("p", null, props.emptyMessage)
        : el("ul", null, items.map((i) => el("li", { key: i.id }))),
    );
  };
}

export function createDashboardSectionRouteCard() {
  return function SectionRouteCard(props: {
    title?: ReactNode;
    description?: ReactNode;
    routes?: Array<{ id: string; label: ReactNode; onClick?: () => void }>;
  }) {
    return el(
      "div",
      null,
      el("h3", null, props.title),
      props.description,
      (props.routes ?? []).map((route) =>
        el(
          "button",
          { key: route.id, type: "button", onClick: route.onClick },
          route.label,
        ),
      ),
    );
  };
}

export function createDashboardCatalogSearchBar() {
  return function CatalogSearchBar(props: {
    value?: string;
    onChange?: (value: string) => void;
    hits?: Array<{ id: string; label: ReactNode; groupLabel?: string }>;
    onSelectHit?: (id: string) => void;
    placeholder?: string;
    "aria-label"?: string;
  }) {
    return el("input", {
      "aria-label": props["aria-label"],
      placeholder: props.placeholder,
      value: props.value ?? "",
      onChange: (event: { target: { value: string } }) =>
        props.onChange?.(event.target.value),
    });
  };
}

export function createDashboardRecentAccessStrip() {
  return function RecentStrip(props: {
    label?: ReactNode;
    items?: Array<{ id: string; label: ReactNode }>;
    onSelect?: (id: string) => void;
  }) {
    const items = props.items ?? [];
    if (!items.length) return null;
    return el(
      "div",
      null,
      el("span", null, props.label),
      items.map((item) =>
        el(
          "button",
          {
            key: item.id,
            type: "button",
            onClick: () => props.onSelect?.(item.id),
          },
          item.label,
        ),
      ),
    );
  };
}

export function createDashboardTopBar() {
  return function TopBar(props: {
    items?: Array<{ id: string; label: ReactNode; onSelect?: () => void }>;
    secondary?: ReactNode;
    actions?: ReactNode;
    "aria-label"?: string;
  }) {
    return el(
      "nav",
      { "aria-label": props["aria-label"] },
      (props.items ?? []).map((item) =>
        el(
          "button",
          { key: item.id, type: "button", onClick: item.onSelect },
          item.label,
        ),
      ),
      props.secondary,
      props.actions,
    );
  };
}

export function createDashboardTopBarUtilityCluster() {
  return function Cluster(props: { children?: ReactNode }) {
    return el("div", null, props.children);
  };
}

export function createDashboardTopBarSearchTrigger() {
  return forwardRef<
    HTMLButtonElement,
    { onOpen?: () => void; label?: ReactNode; "aria-label"?: string }
  >(function SearchTrigger(props, ref) {
    return el(
      "button",
      {
        type: "button",
        ref,
        onClick: props.onOpen,
        "aria-label": props["aria-label"],
      },
      props.label,
    );
  });
}

export function createDashboardTopBarUserIdentity() {
  return function Identity(props: {
    displayName?: string | null;
    fallbackLabel?: string;
  }) {
    return el("span", null, props.displayName ?? props.fallbackLabel);
  };
}

export function createDashboardCommandPalette() {
  return function Palette(props: {
    open?: boolean;
    title?: ReactNode;
    value?: string;
    onChange?: (value: string) => void;
    hits?: Array<{ id: string; label: ReactNode }>;
    onSelectHit?: (id: string) => void;
  }) {
    if (!props.open) return null;
    return el(
      "div",
      { role: "dialog" },
      el("h2", null, props.title),
      el("input", {
        value: props.value ?? "",
        onChange: (event: { target: { value: string } }) =>
          props.onChange?.(event.target.value),
      }),
      (props.hits ?? []).map((hit) =>
        el(
          "button",
          {
            key: hit.id,
            type: "button",
            onClick: () => props.onSelectHit?.(hit.id),
          },
          hit.label,
        ),
      ),
    );
  };
}
