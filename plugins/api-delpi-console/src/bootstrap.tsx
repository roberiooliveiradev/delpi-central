import ReactDOM from "react-dom/client";
import App, { type AppProps } from "./App";

const roots = new WeakMap<HTMLElement, ReactDOM.Root>();

function renderApp(el: HTMLElement, props: AppProps) {
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

const devRoot = document.getElementById("root");
if (devRoot) mount(devRoot);

export default App;
