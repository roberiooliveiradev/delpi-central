import ReactDOM from "react-dom/client";
import { PublicErrorBoundary } from "./shell/PublicErrorBoundary";
import { PublicShell } from "./shell/PublicShell";
import "./shell/brand-tokens.css";
import "./shell/shell.css";

const root = document.getElementById("root");
if (root) {
  try {
    root.dataset.mounted = "1";
    ReactDOM.createRoot(root).render(
      <PublicErrorBoundary>
        <PublicShell />
      </PublicErrorBoundary>,
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : "Erro inesperado.";
    root.innerHTML = `<div class="pub-fallback pub-fallback--fatal"><h1>Não foi possível exibir esta página</h1><p>${message}</p></div>`;
    console.error("[public-hub] bootstrap failed", error);
  }
}
