/**
 * Vite dev — monta o catálogo visual localmente (porta 5010).
 * Em produção o portal carrega `./App` via remoteEntry.js.
 */
import "./styles.css";
import "./app/catalog.css";

import { createRoot } from "react-dom/client";

import CatalogApp from "./app/CatalogApp";

const rootEl = document.getElementById("root");
if (!rootEl) {
  throw new Error("Elemento #root não encontrado no index.html");
}

createRoot(rootEl).render(<CatalogApp />);
