import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App
      isSuperadmin
      permissions={[
        "delpi-mes.access",
        "delpi-mes.monitoring.view",
        "delpi-mes.downtimes.view",
        "delpi-mes.history.view",
        "delpi-mes.view.filial-01",
        "delpi-mes.view.filial-02",
      ]}
    />
  </StrictMode>,
);
