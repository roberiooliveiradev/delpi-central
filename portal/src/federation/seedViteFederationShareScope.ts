/**
 * Registra React (e peers MF) no escopo compartilhado do @originjs/vite-plugin-federation.
 *
 * O portal não é build federado, mas carrega remoteEntry.js dos MFEs via AppHost.
 * Sem este seed, cada MFE e o remote plugin-ui carregam cópias próprias de React → erro #321.
 */
import * as React from "react";
import * as ReactDOM from "react-dom";
import * as LucideReact from "lucide-react";

type FederationShareEntry = {
  get: () => () => Promise<unknown>;
  loaded: 1;
  from: "portal";
};

type FederationShareScope = Record<
  string,
  Record<string, FederationShareEntry>
>;

function shareEntry(mod: unknown): FederationShareEntry {
  return {
    loaded: 1,
    from: "portal",
    get: () => () => Promise.resolve(mod),
  };
}

function registerSharedModule(
  scope: FederationShareScope,
  packageName: string,
  mod: unknown,
  version: string,
) {
  scope[packageName] = scope[packageName] ?? {};
  const entry = shareEntry(mod);
  scope[packageName][version] = entry;
  // Compatível com requiredVersion amplo nos remotes federados.
  scope[packageName]["0.0.0"] = entry;
}

export function seedViteFederationShareScope(): void {
  const globalRef = globalThis as typeof globalThis & {
    __federation_shared__?: Record<string, FederationShareScope>;
  };

  globalRef.__federation_shared__ = globalRef.__federation_shared__ ?? {};
  globalRef.__federation_shared__.default = globalRef.__federation_shared__.default ?? {};

  const scope = globalRef.__federation_shared__.default;

  registerSharedModule(scope, "react", React, React.version);
  registerSharedModule(scope, "react-dom", ReactDOM, ReactDOM.version);
  registerSharedModule(scope, "lucide-react", LucideReact, "0.0.0");
}
