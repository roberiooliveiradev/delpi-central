import ReactDOM from "react-dom/client";
import App, { type AppProps } from "./App";
import "./index.css";

const roots = new WeakMap<HTMLElement, ReactDOM.Root>();

export function mount(el: HTMLElement, props: AppProps = {}) {
  let root = roots.get(el);

  if (!root) {
    root = ReactDOM.createRoot(el);
    roots.set(el, root);
  }

  root.render(<App {...props} />);
}

export function unmount(el?: HTMLElement) {
  if (!el) return;

  const root = roots.get(el);
  if (!root) return;

  root.unmount();
  roots.delete(el);
}
