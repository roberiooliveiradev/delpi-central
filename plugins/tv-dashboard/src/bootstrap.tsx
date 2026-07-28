import "./index.css";

import {
  getReactDomClient,
  preparePluginUiRemote,
} from "../../vite/federationShareScope";

await preparePluginUiRemote();

const ReactDOM = await getReactDomClient();

import type { AppProps } from "./App";
import type { Root } from "react-dom/client";
const { default: App } = await import("./App");

const roots = new WeakMap<HTMLElement, Root>();
/** Fallback quando o host chama unmount sem o elemento (ref já nulo no cleanup). */
let lastMountedEl: HTMLElement | null = null;

function renderApp(el: HTMLElement, props: AppProps = {}) {
  lastMountedEl = el;
  const existing = roots.get(el);
  if (existing) {
    existing.render(<App {...props} />);
    return;
  }

  const created = ReactDOM.createRoot(el);
  if (!created) return;
  roots.set(el, created);
  created.render(<App {...props} />);
}

export function mount(el: HTMLElement, props: AppProps = {}) {
  renderApp(el, props);
}

export function updateRoute(el: HTMLElement, props: AppProps = {}) {
  renderApp(el, props);
}

/**
 * Desmonta o remote. Sem `el`, usa o último host montado — necessário quando o
 * AppHost limpa a ref antes do unmount e o WebSocket de presença ficaria vivo.
 */
export function unmount(el?: HTMLElement | null) {
  const target = el ?? lastMountedEl;
  if (!target) return;

  const root = roots.get(target);
  if (!root) {
    if (lastMountedEl === target) lastMountedEl = null;
    return;
  }

  root.unmount();
  roots.delete(target);
  if (lastMountedEl === target) lastMountedEl = null;
}
