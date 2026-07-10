/**
 * Share scope MF — registra React do MFE pai antes do remote plugin-ui.
 *
 * plugin-ui usa importShared('react'); sem versão explícica no scope o runtime
 * falha (requiredVersion / import:false). Mesma instância que bootstrap/App.
 */
import React from "react";
import * as ReactDOM from "react-dom";
import * as ReactDOMClient from "react-dom/client";
import * as LucideReact from "lucide-react";
import { publishDelpiMfReact } from "./federationReactProxyFix";

type FederationShareFrom = "mfe-host" | "portal-host";

type FederationShareEntry = {
  get: () => () => Promise<unknown>;
  loaded: 1;
  from: FederationShareFrom;
};

type FederationShareScope = Record<string, Record<string, FederationShareEntry>>;

function getShareScope(): FederationShareScope {
  const globalRef = globalThis as typeof globalThis & {
    __federation_shared__?: Record<string, FederationShareScope>;
  };

  globalRef.__federation_shared__ = globalRef.__federation_shared__ ?? {};
  globalRef.__federation_shared__.default = globalRef.__federation_shared__.default ?? {};

  return globalRef.__federation_shared__.default;
}

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
  const packages = getShareScope()[packageName];
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

async function sharedReactDomHasCreateRoot(): Promise<boolean> {
  try {
    const mod = (await loadSharedModule("react-dom")) as Record<string, unknown>;
    return typeof mod.createRoot === "function";
  } catch {
    return false;
  }
}

/**
 * Registra React/lucide no share scope.
 * Usa par portal (react + react-dom) só se o host expõe createRoot — senão par MFE.
 */
export async function ensureMfeFederationShareScopeReady(): Promise<void> {
  const scope = getShareScope();
  const reactDomShared = buildReactDomSharedExport();

  let preservePortalPair =
    hasPortalHostEntry(scope, "react") && hasPortalHostEntry(scope, "react-dom");

  if (preservePortalPair && !(await sharedReactDomHasCreateRoot())) {
    preservePortalPair = false;
  }

  registerModule(scope, "react", React, React.version, "mfe-host", preservePortalPair);
  registerModule(scope, "react-dom", reactDomShared, ReactDOM.version, "mfe-host", preservePortalPair);
  registerModule(scope, "lucide-react", LucideReact, "0.0.0", "mfe-host", true);
  publishDelpiMfReact(React);
}

/** @deprecated Prefer ensureMfeFederationShareScopeReady — sync não valida createRoot do portal. */
export function ensureMfeFederationShareScope(): void {
  const scope = getShareScope();
  const reactDomShared = buildReactDomSharedExport();

  registerModule(scope, "react", React, React.version, "mfe-host", true);
  registerModule(scope, "react-dom", reactDomShared, ReactDOM.version, "mfe-host", false);
  registerModule(scope, "lucide-react", LucideReact, "0.0.0", "mfe-host", true);
  publishDelpiMfReact(React);
}

/** createRoot/hydrateRoot via share scope — mesma instância que importShared('react'). */
export async function getReactDomClient(): Promise<typeof import("react-dom/client")> {
  await ensureMfeFederationShareScopeReady();

  const mod = (await loadSharedModule("react-dom")) as Record<string, unknown>;
  if (typeof mod.createRoot === "function") {
    return mod as typeof import("react-dom/client");
  }

  throw new Error('Shared "react-dom" não expõe createRoot.');
}

/** Bootstrap MFE federado — share scope + CSS do remote plugin-ui. */
export async function preparePluginUiRemote(): Promise<void> {
  await ensureMfeFederationShareScopeReady();
  await import("@delpi/plugin-ui/styles");
}
