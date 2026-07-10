/**
 * Share scope MF — registra React do MFE pai antes do remote plugin-ui.
 *
 * plugin-ui usa importShared('react'); sem versão explícita no scope o runtime
 * falha (requiredVersion / import:false). Mesma instância que bootstrap/App.
 */
import React from "react";
import * as ReactDOM from "react-dom";
import * as LucideReact from "lucide-react";

type FederationShareEntry = {
  get: () => () => Promise<unknown>;
  loaded: 1;
  from: "mfe-host";
};

type FederationShareScope = Record<string, Record<string, FederationShareEntry>>;

function shareEntry(mod: unknown): FederationShareEntry {
  return {
    loaded: 1,
    from: "mfe-host",
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

export function ensureMfeFederationShareScope(): void {
  const globalRef = globalThis as typeof globalThis & {
    __federation_shared__?: Record<string, FederationShareScope>;
  };

  globalRef.__federation_shared__ = globalRef.__federation_shared__ ?? {};
  globalRef.__federation_shared__.default = globalRef.__federation_shared__.default ?? {};

  const scope = globalRef.__federation_shared__.default;

  registerModule(scope, "react", React, React.version);
  registerModule(scope, "react-dom", ReactDOM, ReactDOM.version);
  registerModule(scope, "lucide-react", LucideReact, "0.0.0");
}

/** Bootstrap MFE federado — share scope + CSS do remote plugin-ui. */
export async function preparePluginUiRemote(): Promise<void> {
  ensureMfeFederationShareScope();
  await import("@delpi/plugin-ui/styles");
}
