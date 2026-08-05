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

/** Backstop: falha de SSO nunca pode deixar o portal preso no loader. */
const INIT_TIMEOUT_MS = 20000;

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
    const init = keycloak
      .init({
        onLoad: "check-sso",
        pkceMethod: "S256",
        /**
         * O iframe de status limpa o token local (`clearToken`) a cada resposta
         * diferente de "unchanged" e, sem silent check-sso, a recuperação vira
         * redirect de página inteira — o que gerava recarregamento em loop.
         */
        checkLoginIframe: false,
        silentCheckSsoRedirectUri: `${window.location.origin}/silent-check-sso.html`,
      })
      .then((authenticated) => {
        stripOAuthHash();
        return authenticated;
      });

    const timeout = new Promise<boolean>((resolve) => {
      window.setTimeout(() => resolve(keycloak.authenticated ?? false), INIT_TIMEOUT_MS);
    });

    initPromise = Promise.race([init, timeout]);
  }

  return initPromise;
};

export default keycloak;