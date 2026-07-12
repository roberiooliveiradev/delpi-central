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

function renderApp(el: HTMLElement, props: AppProps = {}) {
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

export function unmount(el?: HTMLElement) {
  if (!el) return;

  const root = roots.get(el);
  if (!root) return;

  root.unmount();
  roots.delete(el);
}
