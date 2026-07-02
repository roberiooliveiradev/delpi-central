import ReactDOM from "react-dom/client";
import { PublicShell } from "./shell/PublicShell";
import "./shell/brand-tokens.css";
import "./shell/shell.css";

const root = document.getElementById("root");
if (root) {
  ReactDOM.createRoot(root).render(<PublicShell />);
}
