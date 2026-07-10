import "./index.css";

import {
  getReactDomClient,
  preparePluginUiRemote,
} from "../../vite/federationShareScope";

await preparePluginUiRemote();

const ReactDOM = await getReactDomClient();

import type { Root } from "react-dom/client";
const { default: App } = await import("./App");

export type AppProps = {
  getAccessToken?: () => string | undefined;
  pathname?: string;
  search?: string;
};

const roots = new WeakMap<HTMLElement, Root>();

function renderApp(el: HTMLElement, props: AppProps = {}) {
  let root = roots.get(el);

  if (!root) {
    root = ReactDOM.createRoot(el);
    roots.set(el, root);
  }

  root.render(<App {...props} />);
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
