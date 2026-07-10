import ReactDOM from "react-dom/client";
import { resolvePropostasComerciaisRouteKey } from "./utils/route";
import "./index.css";

import { preparePluginUiRemote } from "../../vite/federationShareScope";

await preparePluginUiRemote();

import type { AppProps } from "./App";
const { default: App } = await import("./App");

const roots = new WeakMap<HTMLElement, ReactDOM.Root>();

function renderApp(el: HTMLElement, props: AppProps = {}) {
  let root = roots.get(el);

  if (!root) {
    root = ReactDOM.createRoot(el);
    roots.set(el, root);
  }

  const routeKey = resolvePropostasComerciaisRouteKey(props.pathname);
  root.render(<App key={routeKey} {...props} />);
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
