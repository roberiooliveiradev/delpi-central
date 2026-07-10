// src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./ui/App";
import { AuthProvider } from "./state/AuthContext";
import { NotificationCatalogProvider } from "./state/NotificationCatalogContext";
import { seedViteFederationShareScope } from "./federation/seedViteFederationShareScope";
import "./index.css";

seedViteFederationShareScope();

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