export const APP_BASE = "/apps/customer-experience";

export type CxTab = "participants" | "forms";
export type FormsView = "list" | "editor" | "dashboard";

export type CxRoute = {
  tab: CxTab;
  formsView: FormsView;
  formId?: string;
};

function normalizePath(pathname?: string): string {
  const path = (pathname ?? APP_BASE).trim() || APP_BASE;
  return path.replace(/\/+$/, "") || APP_BASE;
}

export function parseRoute(pathname?: string): CxRoute {
  const path = normalizePath(pathname);
  const suffix = path.startsWith(APP_BASE) ? path.slice(APP_BASE.length) : path;
  const segments = suffix.split("/").filter(Boolean);

  if (segments[0] === "formularios") {
    const formId = segments[1];
    if (formId && segments[2] === "respostas") {
      return { tab: "forms", formsView: "dashboard", formId };
    }
    if (formId) {
      return { tab: "forms", formsView: "editor", formId };
    }
    return { tab: "forms", formsView: "list" };
  }

  if (segments[0] === "participantes") {
    return { tab: "participants", formsView: "list" };
  }

  return { tab: "participants", formsView: "list" };
}

export function participantsPath(): string {
  return `${APP_BASE}/participantes`;
}

export function formsListPath(): string {
  return `${APP_BASE}/formularios`;
}

export function formEditPath(formId: string): string {
  return `${APP_BASE}/formularios/${formId}`;
}

export function formDashboardPath(formId: string): string {
  return `${APP_BASE}/formularios/${formId}/respostas`;
}
