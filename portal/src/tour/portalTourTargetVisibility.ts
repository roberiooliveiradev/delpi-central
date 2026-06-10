import type { PortalTourQuest } from "./portalTourQuestTypes";
import {
  isAdminRoute,
  isDedicatedTourPage,
  isHomeRoute,
  isNotificationsRoute,
  isPrivacyRoute,
  isProfileRoute,
} from "./portalTourRoutes";

export type TourHighlightRect = {
  questId: string;
  top: number;
  left: number;
  width: number;
  height: number;
};

const HIGHLIGHT_PAD = 3;
const MIN_SIZE = 12;
const MAX_RING_SIZE = 280;

const HIGHLIGHT_PRIORITY: Record<string, number> = {
  "pin-app": 100,
  "launcher-search": 98,
  "open-apps": 95,
  "sidebar-favorites": 85,
  "page-notifications-inbox": 84,
  "page-notifications-filter": 83,
  "page-notifications-preferences": 82,
  "page-profile-info": 81,
  "page-profile-rbac": 80,
  "page-admin-users": 79,
  "home-summary-notifications": 78,
  "home-favorites": 77,
  "home-recent": 76,
  "home-notifications": 75,
  "sidebar-notifications": 60,
  "sidebar-theme": 59,
  "sidebar-profile": 58,
  "page-privacy-consent": 57,
  "page-privacy-export": 56,
  "page-profile-apps": 55,
  "page-profile-tour-restart": 54,
  "profile-tour-resume": 54,
  "sidebar-admin": 53,
  "page-admin-roles": 52,
  "page-admin-permissions": 51,
  "page-admin-apps": 50,
};

export function isLauncherOpen() {
  const modal = document.querySelector('[data-tour="launcher-modal"]');
  if (!modal) return false;
  return isElementVisibleForTour(modal);
}

function isInLauncherModal(element: Element) {
  return Boolean(element.closest('[data-tour="launcher-modal"]'));
}

function isInSidebar(element: Element) {
  return Boolean(element.closest(".sidebar"));
}

function isInHomeSection(element: Element) {
  return Boolean(
    element.closest("#home-page, #home-favorites, #home-recent, #home-notifications"),
  );
}

function isInPageRoot(element: Element, selector: string) {
  return Boolean(element.closest(selector));
}

export function isElementVisibleForTour(element: Element): boolean {
  if (!(element instanceof HTMLElement)) return false;

  const style = window.getComputedStyle(element);
  if (style.display === "none" || style.visibility === "hidden") return false;
  if (Number.parseFloat(style.opacity) < 0.12) return false;

  let parent = element.parentElement;
  while (parent) {
    const parentStyle = window.getComputedStyle(parent);
    if (parentStyle.display === "none" || parentStyle.visibility === "hidden") {
      return false;
    }
    if (Number.parseFloat(parentStyle.opacity) < 0.08) {
      return false;
    }
    parent = parent.parentElement;
  }

  const rect = element.getBoundingClientRect();
  if (rect.width < MIN_SIZE || rect.height < MIN_SIZE) return false;

  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  const visibleWidth =
    Math.min(rect.right, viewportWidth) - Math.max(rect.left, 0);
  const visibleHeight =
    Math.min(rect.bottom, viewportHeight) - Math.max(rect.top, 0);

  if (visibleWidth < MIN_SIZE || visibleHeight < MIN_SIZE) return false;

  const visibleArea = visibleWidth * visibleHeight;
  const totalArea = rect.width * rect.height;
  if (totalArea > 0 && visibleArea / totalArea < 0.55) return false;

  return true;
}

export function queryFirstVisible(selector: string): HTMLElement | null {
  for (const element of document.querySelectorAll(selector)) {
    if (isElementVisibleForTour(element)) {
      return element as HTMLElement;
    }
  }
  return null;
}

export function hasVisibleTarget(selector: string) {
  return queryFirstVisible(selector) !== null;
}

function resolveQuestHighlightSelector(quest: PortalTourQuest) {
  if (quest.highlightSelector) return quest.highlightSelector;
  return quest.actionSelector.split(",")[0]?.trim() ?? quest.actionSelector;
}

function isQuestAvailable(quest: PortalTourQuest) {
  return quest.isAvailable ? quest.isAvailable() : true;
}

function scopeMatchesRoute(scope: PortalTourQuest["scope"]) {
  switch (scope) {
    case "home":
      return isHomeRoute();
    case "profile":
      return isProfileRoute();
    case "notifications":
      return isNotificationsRoute();
    case "privacy":
      return isPrivacyRoute();
    case "admin":
      return isAdminRoute();
    case "sidebar":
    case "launcher":
      return !isDedicatedTourPage();
    default:
      return true;
  }
}

function shouldHighlightQuest(quest: PortalTourQuest) {
  if (!isQuestAvailable(quest)) return false;

  if (isLauncherOpen()) {
    return quest.scope === "launcher";
  }

  if (quest.scope === "launcher") return false;

  if (isDedicatedTourPage()) {
    if (quest.scope === "sidebar" || quest.scope === "home") return false;
    return scopeMatchesRoute(quest.scope);
  }

  if (quest.scope === "home") return isHomeRoute();
  if (quest.scope === "sidebar") return true;
  if (
    quest.scope === "profile" ||
    quest.scope === "notifications" ||
    quest.scope === "privacy" ||
    quest.scope === "admin"
  ) {
    return false;
  }

  return true;
}

function matchesHighlightContext(quest: PortalTourQuest, element: HTMLElement) {
  if (isLauncherOpen()) {
    return quest.scope === "launcher" && isInLauncherModal(element);
  }

  switch (quest.scope) {
    case "launcher":
      return false;
    case "sidebar":
      return isInSidebar(element);
    case "home":
      return isHomeRoute() && isInHomeSection(element);
    case "profile":
      return isProfileRoute() && isInPageRoot(element, '[data-tour="profile-page"], #profile-info, .home-wrap');
    case "notifications":
      return (
        isNotificationsRoute() &&
        isInPageRoot(element, '[data-tour="notifications-page"]')
      );
    case "privacy":
      return (
        isPrivacyRoute() &&
        isInPageRoot(element, '[data-tour="privacy-page"]')
      );
    case "admin":
      return (
        isAdminRoute() &&
        isInPageRoot(element, '[data-tour="admin-page"]')
      );
    default:
      return true;
  }
}

function resolveHighlightElements(quest: PortalTourQuest): HTMLElement[] {
  if (!shouldHighlightQuest(quest)) return [];

  const selector = resolveQuestHighlightSelector(quest);
  const element = queryFirstVisible(selector);
  const elements = element ? [element] : [];

  return elements.filter((item) => matchesHighlightContext(quest, item));
}

function measureElement(
  questId: string,
  element: HTMLElement,
): TourHighlightRect | null {
  if (!isElementVisibleForTour(element)) return null;

  const rect = element.getBoundingClientRect();
  if (rect.width < MIN_SIZE || rect.height < MIN_SIZE) return null;
  if (rect.width > MAX_RING_SIZE || rect.height > MAX_RING_SIZE) return null;

  return {
    questId,
    top: rect.top - HIGHLIGHT_PAD,
    left: rect.left - HIGHLIGHT_PAD,
    width: rect.width + HIGHLIGHT_PAD * 2,
    height: rect.height + HIGHLIGHT_PAD * 2,
  };
}

export function resolveQuestHighlights(
  quests: PortalTourQuest[],
  completedIds: ReadonlySet<string>,
): TourHighlightRect[] {
  const launcherOpen = isLauncherOpen();
  const maxHighlights = launcherOpen ? 1 : window.innerWidth <= 768 ? 1 : 2;

  const candidates = quests
    .filter((quest) => !completedIds.has(quest.id))
    .flatMap((quest) =>
      resolveHighlightElements(quest).map((element) => ({
        quest,
        element,
        priority: HIGHLIGHT_PRIORITY[quest.id] ?? 0,
      })),
    )
    .map(({ quest, element, priority }) => {
      const rect = measureElement(quest.id, element);
      return rect ? { rect, priority } : null;
    })
    .filter((item): item is { rect: TourHighlightRect; priority: number } =>
      Boolean(item),
    )
    .sort((a, b) => b.priority - a.priority);

  return candidates.slice(0, maxHighlights).map((item) => item.rect);
}

// Re-export for backwards compatibility in quest modules
export { isHomeRoute } from "./portalTourRoutes";
