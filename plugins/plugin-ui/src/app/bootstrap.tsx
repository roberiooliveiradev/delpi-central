/**
 * Entry Module Federation `./App` — catálogo visual montado pelo portal.
 * Não chama preparePluginUiRemote: este pacote É o remote da biblioteca.
 */
import "../styles.css";
import "./catalog.css";

import { createRoot, type Root } from "react-dom/client";

import CatalogApp, { type AppProps } from "./CatalogApp";

const roots = new WeakMap<HTMLElement, Root>();

function renderApp(el: HTMLElement, props: AppProps = {}) {
  let root = roots.get(el);
  if (!root) {
    root = createRoot(el);
    roots.set(el, root);
  }
  root.render(<CatalogApp {...props} />);
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
