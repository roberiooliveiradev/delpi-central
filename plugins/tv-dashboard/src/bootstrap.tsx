import ReactDOM from "react-dom/client";
import App, { type AppProps } from "./App";
import "./index.css";

import { preparePluginUiRemote } from "../../vite/federationShareScope";
await preparePluginUiRemote();

/** Legado: removida do portal; limpa instalações com classe presa no html. */
const LEGACY_PORTAL_LAYOUT_CLASS = "tv-dashboard-deck-active";

const roots = new WeakMap<HTMLElement, ReactDOM.Root>();

function resetLegacyPortalLayoutClass() {
  document.documentElement.classList.remove(LEGACY_PORTAL_LAYOUT_CLASS);
}

function renderApp(el: HTMLElement, props: AppProps = {}) {
  let root = roots.get(el);
  if (!root) {
    root = ReactDOM.createRoot(el);
    roots.set(el, root);
  }
  root.render(<App {...props} />);
}

export function mount(el: HTMLElement, props: AppProps = {}) {
  resetLegacyPortalLayoutClass();
  renderApp(el, props);
}

export function updateRoute(el: HTMLElement, props: AppProps = {}) {
  renderApp(el, props);
}

export function unmount(el?: HTMLElement) {
  resetLegacyPortalLayoutClass();
  if (!el) return;
  const root = roots.get(el);
  if (!root) return;
  root.unmount();
  roots.delete(el);
}
