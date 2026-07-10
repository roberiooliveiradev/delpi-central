/**
 * Share scope MF no portal — uma instância de React para o shell e todos os MFEs.
 *
 * O portal carrega remotes via AppHost; semear React aqui antes de container.init
 * evita importShared cair em cópia bundled do plugin-ui (React #321).
 */
import React from "react";
import * as ReactDOM from "react-dom";
import * as ReactDOMClient from "react-dom/client";
import * as LucideReact from "lucide-react";

type FederationShareEntry = {
  get: () => () => Promise<unknown>;
  loaded: 1;
  from: "portal-host";
};

type FederationShareScope = Record<string, Record<string, FederationShareEntry>>;

function buildReactDomSharedExport() {
  return {
    ...ReactDOM,
    createRoot: ReactDOMClient.createRoot,
    hydrateRoot: ReactDOMClient.hydrateRoot,
  };
}

function shareEntry(mod: unknown): FederationShareEntry {
  return {
    loaded: 1,
    from: "portal-host",
    get: () => () => Promise.resolve(mod),
  };
}

function registerModule(
  scope: FederationShareScope,
  packageName: string,
  mod: unknown,
  version: string,
) {
  scope[packageName] = scope[packageName] ?? {};
  const entry = shareEntry(mod);
  scope[packageName][version] = entry;
  scope[packageName]["0.0.0"] = entry;
}

export function ensurePortalFederationShareScope(): void {
  const globalRef = globalThis as typeof globalThis & {
    __federation_shared__?: Record<string, FederationShareScope>;
  };

  globalRef.__federation_shared__ = globalRef.__federation_shared__ ?? {};
  globalRef.__federation_shared__.default = globalRef.__federation_shared__.default ?? {};

  const scope = globalRef.__federation_shared__.default;
  const reactDomShared = buildReactDomSharedExport();

  registerModule(scope, "react", React, React.version);
  registerModule(scope, "react-dom", reactDomShared, ReactDOM.version);
  registerModule(scope, "lucide-react", LucideReact, "0.0.0");

  (globalThis as Record<string, unknown>).__DELPI_MF_REACT__ = React;
}
