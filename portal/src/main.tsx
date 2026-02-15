// src/main.tsx

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./ui/App";
import { AuthProvider } from "./state/AuthContext";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <App />
    </AuthProvider>
  </React.StrictMode>
);
