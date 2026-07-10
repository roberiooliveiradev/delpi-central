// src/main.tsx
import { ensurePortalFederationShareScope } from "./utils/federationShareScope";

ensurePortalFederationShareScope();

import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./ui/App";
import { AuthProvider } from "./state/AuthContext";
import { NotificationCatalogProvider } from "./state/NotificationCatalogContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <NotificationCatalogProvider>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </NotificationCatalogProvider>
    </AuthProvider>
  </React.StrictMode>
);