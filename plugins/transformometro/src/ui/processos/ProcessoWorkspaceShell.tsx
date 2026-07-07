import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import {
  fetchProcesso,
  fetchProcessoInstancias,
  fetchRevisoes,
  type Processo,
  type ProcessoInstancia,
  type Revisao,
} from "../../data/api/transformometroApi";
import { ProcessoWorkspaceSidebar } from "./ProcessoWorkspaceSidebar";
import {
  buildProcessoWorkspaceTree,
  parseProcessoSectionFromHash,
  type ProcessoWorkspaceSectionId,
} from "./processoWorkspaceNav";

type Props = {
  processoId: string;
  activeNodeId: string;
  getAccessToken?: () => string | undefined;
  onNavigate: (href: string) => void;
  children: ReactNode;
  processo?: Processo | null;
  instancias?: ProcessoInstancia[];
  revisoes?: Revisao[];
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
}: Props) {
  const [processo, setProcesso] = useState<Processo | null>(processoProp ?? null);
  const [instancias, setInstancias] = useState<ProcessoInstancia[]>(instanciasProp ?? []);
  const [revisoes, setRevisoes] = useState<Revisao[]>(revisoesProp ?? []);

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

  const treeNodes = useMemo(() => {
    if (!processo) return [];
    return buildProcessoWorkspaceTree({ processo, instancias, revisoes });
  }, [instancias, processo, revisoes]);

  return (
    <div className="tm-processo-workspace">
      <ProcessoWorkspaceSidebar
        processoCode={processo?.codigo_processo ?? "…"}
        processoLabel={processo?.nome_processo ?? "Processo"}
        nodes={treeNodes}
        activeNodeId={activeNodeId}
        onNavigate={onNavigate}
      />
      <div className="tm-processo-workspace__main">
        <div key={activeNodeId} className="tm-processo-workspace__panel">
          {children}
        </div>
      </div>
    </div>
  );
}

export function useProcessoWorkspaceSection(): ProcessoWorkspaceSectionId {
  const readHash = () => (typeof window !== "undefined" ? window.location.hash : "");

  const [section, setSection] = useState<ProcessoWorkspaceSectionId>(() =>
    parseProcessoSectionFromHash(readHash())
  );

  useEffect(() => {
    const sync = () => setSection(parseProcessoSectionFromHash(readHash()));
    sync();
    window.addEventListener("hashchange", sync);
    return () => window.removeEventListener("hashchange", sync);
  }, []);

  return section;
}
