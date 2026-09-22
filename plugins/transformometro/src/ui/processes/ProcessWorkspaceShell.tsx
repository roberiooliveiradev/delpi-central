import type { CSSProperties, ReactNode } from "react";
import { useSyncExternalStore } from "react";

import { TRANSFORMOMETRO_WORKSPACE_HASH_EVENT } from "../../utils/navigation";
import {
  defaultInstanciaSection,
  defaultRevisaoSection,
  parseInstanciaSectionFromHash,
  parseProcessoSectionFromHash,
  parseRevisaoSectionFromHash,
  type InstanciaWorkspaceSectionId,
  type ProcessoWorkspaceSectionId,
  type RevisaoWorkspaceSectionId,
} from "./processWorkspaceNav";
import { ProcessWorkspacePanelActionsProvider } from "./processWorkspacePanelActions";

type Props = {
  children: ReactNode;
  /** Faixa superior: path + hero + nav horizontal. */
  chrome?: ReactNode;
  className?: string;
  style?: CSSProperties;
};

/**
 * Shell do Process Workspace — conteúdo em largura total.
 * Navegação primária é horizontal (UnderlineNav), não árvore de pastas.
 */
export function ProcessWorkspaceShell({ children, chrome, className, style }: Props) {
  const rootClass = ["tm-processo-workspace", "tm-processo-workspace--flat", className]
    .filter(Boolean)
    .join(" ");

  return (
    <ProcessWorkspacePanelActionsProvider>
      <div className={rootClass} style={style}>
        {chrome ? <div className="tm-processo-workspace__chrome">{chrome}</div> : null}
        <div className="tm-processo-workspace__main">
          <div className="tm-processo-workspace__sections">{children}</div>
        </div>
      </div>
    </ProcessWorkspacePanelActionsProvider>
  );
}

function subscribeWorkspaceSection(onStoreChange: () => void) {
  window.addEventListener("hashchange", onStoreChange);
  window.addEventListener("popstate", onStoreChange);
  window.addEventListener(TRANSFORMOMETRO_WORKSPACE_HASH_EVENT, onStoreChange);
  return () => {
    window.removeEventListener("hashchange", onStoreChange);
    window.removeEventListener("popstate", onStoreChange);
    window.removeEventListener(TRANSFORMOMETRO_WORKSPACE_HASH_EVENT, onStoreChange);
  };
}

function readWorkspaceSectionSnapshot(): ProcessoWorkspaceSectionId {
  return parseProcessoSectionFromHash(window.location.hash);
}

export function useProcessoWorkspaceSection(): ProcessoWorkspaceSectionId {
  return useSyncExternalStore(
    subscribeWorkspaceSection,
    readWorkspaceSectionSnapshot,
    () => "visao-geral",
  );
}

function readRevisaoSectionSnapshot(cenarioTipo?: string | null): RevisaoWorkspaceSectionId {
  return parseRevisaoSectionFromHash(window.location.hash, cenarioTipo);
}

export function useRevisaoWorkspaceSection(cenarioTipo?: string | null): RevisaoWorkspaceSectionId {
  return useSyncExternalStore(
    subscribeWorkspaceSection,
    () => readRevisaoSectionSnapshot(cenarioTipo),
    () => defaultRevisaoSection(cenarioTipo),
  );
}

function readInstanciaSectionSnapshot(): InstanciaWorkspaceSectionId {
  return parseInstanciaSectionFromHash(window.location.hash);
}

export function useInstanciaWorkspaceSection(): InstanciaWorkspaceSectionId {
  return useSyncExternalStore(
    subscribeWorkspaceSection,
    readInstanciaSectionSnapshot,
    () => defaultInstanciaSection(),
  );
}
