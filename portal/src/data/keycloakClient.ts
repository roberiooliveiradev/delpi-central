// src/data/keycloakClient.ts

import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
  url: "http://localhost/auth",
  realm: "delpi",
  clientId: "delpi-central",
});

// 🔒 Controle interno para evitar init duplicado
let initPromise: Promise<boolean> | null = null;

export const initKeycloak = () => {
  if (!initPromise) {
    initPromise = keycloak.init({
      onLoad: "check-sso",
      pkceMethod: "S256",
      checkLoginIframe: true,
      silentCheckSsoRedirectUri:
        window.location.origin + "/silent-check-sso.html",
    });
  }

  return initPromise;
};

export default keycloak;