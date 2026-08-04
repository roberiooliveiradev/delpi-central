/**
 * Bootstrap do remote parcial `./EmbeddedChat` (Module Federation).
 * Hosts (TV Dashboard) montam o copiloto sem carregar o App completo do portal.
 */
import "./index.css";

import {
  getReactDomClient,
  preparePluginUiRemote,
} from "../../vite/federationShareScope";

await preparePluginUiRemote();

const ReactDOM = await getReactDomClient();

import type { Root } from "react-dom/client";
import EmbeddedChat, {
  type EmbeddedChatProps,
} from "./EmbeddedChat";

const roots = new WeakMap<HTMLElement, Root>();

function render(el: HTMLElement, props: EmbeddedChatProps = {}) {
  let root = roots.get(el);
  if (!root) {
    root = ReactDOM.createRoot(el);
    roots.set(el, root);
  }
  root.render(<EmbeddedChat {...props} />);
}

export type { EmbeddedChatProps, TvWorkspaceContext, EmbeddedChatHostCallbacks } from "./EmbeddedChat";

export function mount(el: HTMLElement, props?: EmbeddedChatProps) {
  render(el, props ?? {});
}

export function update(el: HTMLElement, props?: EmbeddedChatProps) {
  render(el, props ?? {});
}

export function unmount(el?: HTMLElement) {
  if (!el) return;
  const root = roots.get(el);
  if (!root) return;
  root.unmount();
  roots.delete(el);
}
