// src/data/keycloakClient.ts

import Keycloak from "keycloak-js";

const kcUrl = import.meta.env.VITE_KC_URL as string;
const kcRealm = import.meta.env.VITE_KC_REALM as string;
const kcClientId = import.meta.env.VITE_KC_CLIENT_ID as string;

// opcional: logs para debug (remova depois se quiser)
if (!kcUrl || !kcRealm || !kcClientId) {
  // eslint-disable-next-line no-console
  console.warn("Keycloak env missing:", { kcUrl, kcRealm, kcClientId });
}

const keycloak = new Keycloak({
  url: kcUrl,
  realm: kcRealm,
  clientId: kcClientId,
});

// 🔒 Controle interno para evitar init duplicado
let initPromise: Promise<boolean> | null = null;

/** Remove fragmento OAuth da URL após redirect do Keycloak (evita reprocessamento no refresh). */
export function stripOAuthHash(): void {
  const { hash, pathname, search } = window.location;

  if (!hash) {
    return;
  }

  if (!/(^#|[&#])(state|session_state|code|iss)=/.test(hash)) {
    return;
  }

  window.history.replaceState(window.history.state, "", `${pathname}${search}`);
}

export const initKeycloak = () => {
  if (!initPromise) {
    initPromise = keycloak
      .init({
        onLoad: "check-sso",
        pkceMethod: "S256",
        // Iframe de SSO quebra fácil em localhost (cookies/third-party) e gera loop de login.
        checkLoginIframe: import.meta.env.PROD,
      })
      .then((authenticated) => {
        stripOAuthHash();
        return authenticated;
      });
  }

  return initPromise;
};

export default keycloak;