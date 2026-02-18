// src/data/keycloakClient.ts

import Keycloak from "keycloak-js";

const keycloak = new Keycloak({
  url: "http://localhost/auth", 
  realm: "delpi",
  clientId: "delpi-central",
});

export default keycloak;
