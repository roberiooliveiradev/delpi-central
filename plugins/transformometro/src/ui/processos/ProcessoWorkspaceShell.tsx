import { useCallback, useEffect, useMemo, useState, useSyncExternalStore, type ReactNode } from "react";

import {
  fetchProcesso,
  fetchProcessoInstancias,
  fetchRevisoes,
  type Processo,
  type ProcessoInstancia,
  type Revisao,
} from "../../data/api/transformometroApi";
import {
  fetchInstanciaMatrizImpactoEsforco,
  type MatrizImpactoPonto,
} from "../../data/api/transformometroMatrixApi";
import { TRANSFORMOMETRO_WORKSPACE_HASH_EVENT } from "../../utils/navigation";
import { ProcessoWorkspaceSidebar } from "./ProcessoWorkspaceSidebar";
import {
  buildProcessoWorkspaceTree,
  parseProcessoSectionFromHash,
  type ProcessoWorkspaceSectionId,
} from "./processoWorkspaceNav";
import { ProcessoWorkspacePanelActionsProvider } from "./processoWorkspacePanelActions";

type Props = {
  processoId: string;
  activeNodeId: string;
  getAccessToken?: () => string | undefined;
  onNavigate: (href: string) => void;
  children: ReactNode;
  processo?: Processo | null;
  instancias?: ProcessoInstancia[];
  revisoes?: Revisao[];
  backActions?: ReactNode;
  processActions?: ReactNode;
};

export function ProcessoWorkspaceShell({
  processoId,
  activeNodeId,
  getAccessToken,
  onNavigate,
  children,
  processo: processoProp,
  instancias: instanciasProp,
  revisoes: revisoesProp,
  backActions,
  processActions,
}: Props) {
  const [processo, setProcesso] = useState<Processo | null>(processoProp ?? null);
  const [instancias, setInstancias] = useState<ProcessoInstancia[]>(instanciasProp ?? []);
  const [revisoes, setRevisoes] = useState<Revisao[]>(revisoesProp ?? []);
  const [matrixByRevisaoId, setMatrixByRevisaoId] = useState<Record<string, MatrizImpactoPonto>>({});

  const loadSidebarData = useCallback(async () => {
    if (processoProp && instanciasProp && revisoesProp) return;
    try {
      const [proc, inst, revs] = await Promise.all([
        processoProp ? Promise.resolve(processoProp) : fetchProcesso(processoId, getAccessToken),
        instanciasProp
          ? Promise.resolve({ items: instanciasProp })
          : fetchProcessoInstancias(processoId, getAccessToken),
        revisoesProp ? Promise.resolve({ items: revisoesProp }) : fetchRevisoes(processoId, getAccessToken),
      ]);
      if (!processoProp) setProcesso(proc);
      if (!instanciasProp) setInstancias(inst.items);
      if (!revisoesProp) setRevisoes(revs.items);
    } catch {
      if (!processoProp) setProcesso(null);
    }
  }, [getAccessToken, instanciasProp, processoId, processoProp, revisoesProp]);

  useEffect(() => {
    setProcesso(processoProp ?? null);
    setInstancias(instanciasProp ?? []);
    setRevisoes(revisoesProp ?? []);
  }, [instanciasProp, processoProp, revisoesProp]);

  useEffect(() => {
    void loadSidebarData();
  }, [loadSidebarData]);

  useEffect(() => {
    if (instancias.length === 0) {
      setMatrixByRevisaoId({});
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        const responses = await Promise.all(
          instancias.map((instancia) =>
            fetchInstanciaMatrizImpactoEsforco(instancia.instancia_id, getAccessToken, {
              incluir_baseline: true,
            })
          )
        );
        if (cancelled) return;
        const next: Record<string, MatrizImpactoPonto> = {};
        for (const response of responses) {
          for (const ponto of response.pontos) {
            next[ponto.revisao_id] = ponto;
          }
        }
        setMatrixByRevisaoId(next);
      } catch {
        if (!cancelled) setMatrixByRevisaoId({});
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [getAccessToken, instancias]);

  const treeNodes = useMemo(() => {
    if (!processo) return [];
    return buildProcessoWorkspaceTree({ processo, instancias, revisoes, matrixByRevisaoId });
  }, [instancias, matrixByRevisaoId, processo, revisoes]);

  return (
    <ProcessoWorkspacePanelActionsProvider>
      <div className="tm-processo-workspace">
        <ProcessoWorkspaceSidebar
          processoCode={processo?.codigo_processo ?? "…"}
          processoLabel={processo?.nome_processo ?? "Processo"}
          nodes={treeNodes}
          activeNodeId={activeNodeId}
          onNavigate={onNavigate}
          backActions={backActions}
          processActions={processActions}
        />
        <div className="tm-processo-workspace__main">
          <div className="tm-processo-workspace__sections">{children}</div>
        </div>
      </div>
    </ProcessoWorkspacePanelActionsProvider>
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
    () => "visao-geral"
  );
}
