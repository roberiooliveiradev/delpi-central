import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { preparePluginUiRemote } from "../../vite/federationShareScope";
import App from "./App";
import "./index.css";

try {
  await preparePluginUiRemote();
} catch (err) {
  console.warn("[tv-dashboard] plugin-ui remote indisponível no standalone:", err);
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
