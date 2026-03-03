// src/bootstrap.tsx
import ReactDOM from "react-dom/client";
import App from "./App";

let root: ReactDOM.Root | null = null;

export function mount(el: HTMLElement, props: any) {
  root = ReactDOM.createRoot(el);
  root.render(<App {...props} />);
}

export function unmount() {
  root?.unmount();
  root = null;
}