export function normalizePath(pathname: string) {
  const path = pathname.replace(/\/+$/, "") || "/";
  return path;
}

export function isHomeRoute(pathname = window.location.pathname) {
  return normalizePath(pathname) === "/";
}

export function isProfileRoute(pathname = window.location.pathname) {
  return normalizePath(pathname) === "/profile";
}

export function isNotificationsRoute(pathname = window.location.pathname) {
  return normalizePath(pathname) === "/notifications";
}

export function isPrivacyRoute(pathname = window.location.pathname) {
  return normalizePath(pathname) === "/privacy";
}

export function isAdminRoute(pathname = window.location.pathname) {
  return normalizePath(pathname) === "/admin";
}

export function isDedicatedTourPage(pathname = window.location.pathname) {
  return (
    isProfileRoute(pathname) ||
    isNotificationsRoute(pathname) ||
    isPrivacyRoute(pathname) ||
    isAdminRoute(pathname)
  );
}

export function resolveTourContextLabel(pathname = window.location.pathname) {
  if (isAdminRoute(pathname)) return "Painel Admin";
  if (isNotificationsRoute(pathname)) return "Notificações";
  if (isProfileRoute(pathname)) return "Meu Perfil";
  if (isPrivacyRoute(pathname)) return "Privacidade e Dados";
  if (normalizePath(pathname) !== "/" && !isHomeRoute(pathname)) {
    return "Explorando o portal";
  }
  return null;
}
