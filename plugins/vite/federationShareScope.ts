/**
 * Share scope MF — registra React do MFE pai antes do remote plugin-ui.
 *
 * plugin-ui usa importShared('react'); sem versão explícita no scope o runtime
 * falha (requiredVersion / import:false). Mesma instância que bootstrap/App.
 */
import React from "react";
import * as ReactDOM from "react-dom";
import * as ReactDOMClient from "react-dom/client";
import * as LucideReact from "lucide-react";

type FederationShareFrom = "mfe-host" | "portal-host";

type FederationShareEntry = {
  get: () => () => Promise<unknown>;
  loaded: 1;
  from: FederationShareFrom;
};

type FederationShareScope = Record<string, Record<string, FederationShareEntry>>;

function buildReactDomSharedExport() {
  return {
    ...ReactDOM,
    createRoot: ReactDOMClient.createRoot,
    hydrateRoot: ReactDOMClient.hydrateRoot,
  };
}

function shareEntry(mod: unknown, from: FederationShareFrom): FederationShareEntry {
  return {
    loaded: 1,
    from,
    get: () => () => Promise.resolve(mod),
  };
}

function hasPortalHostEntry(scope: FederationShareScope, packageName: string): boolean {
  const versions = scope[packageName];
  if (!versions) return false;
  return Object.values(versions).some((entry) => entry?.from === "portal-host");
}

function registerModule(
  scope: FederationShareScope,
  packageName: string,
  mod: unknown,
  version: string,
  from: FederationShareFrom,
  preservePortalHost = false,
) {
  if (preservePortalHost && hasPortalHostEntry(scope, packageName)) {
    return;
  }

  scope[packageName] = scope[packageName] ?? {};
  const entry = shareEntry(mod, from);
  scope[packageName][version] = entry;
  scope[packageName]["0.0.0"] = entry;
}

export async function loadSharedModule(packageName: string): Promise<unknown> {
  const globalRef = globalThis as typeof globalThis & {
    __federation_shared__?: Record<string, FederationShareScope>;
  };
  const packages = globalRef.__federation_shared__?.default?.[packageName];
  if (!packages) {
    throw new Error(`Module Federation share scope missing "${packageName}".`);
  }

  const versionKey = Object.keys(packages).find((key) => key !== "0.0.0") ?? "0.0.0";
  const entry = packages[versionKey] ?? packages["0.0.0"];
  if (!entry?.get) {
    throw new Error(`Module Federation share entry invalid for "${packageName}".`);
  }

  return (await entry.get())();
}

/** createRoot/hydrateRoot via share scope — mesma instância que importShared('react'). */
export async function getReactDomClient(): Promise<typeof import("react-dom/client")> {
  ensureMfeFederationShareScope();
  const mod = (await loadSharedModule("react-dom")) as Record<string, unknown>;
  if (typeof mod.createRoot === "function") {
    return mod as typeof import("react-dom/client");
  }

  throw new Error('Shared "react-dom" não expõe createRoot.');
}

export function ensureMfeFederationShareScope(): void {
  const globalRef = globalThis as typeof globalThis & {
    __federation_shared__?: Record<string, FederationShareScope>;
  };

  globalRef.__federation_shared__ = globalRef.__federation_shared__ ?? {};
  globalRef.__federation_shared__.default = globalRef.__federation_shared__.default ?? {};

  const scope = globalRef.__federation_shared__.default;
  const reactDomShared = buildReactDomSharedExport();

  registerModule(scope, "react", React, React.version, "mfe-host", true);
  registerModule(scope, "react-dom", reactDomShared, ReactDOM.version, "mfe-host", true);
  registerModule(scope, "lucide-react", LucideReact, "0.0.0", "mfe-host", true);
}

/** Bootstrap MFE federado — share scope + CSS do remote plugin-ui. */
export async function preparePluginUiRemote(): Promise<void> {
  ensureMfeFederationShareScope();
  await import("@delpi/plugin-ui/styles");
}
