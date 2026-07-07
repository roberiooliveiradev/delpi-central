import { useEffect, useMemo, useState } from "react";

import type { AppProps } from "../../App";
import { TransformometroShell } from "../../components/TransformometroShell";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  fetchProcesso,
  fetchProcessoInstancias,
  fetchRevisoes,
  type Processo,
  type ProcessoInstancia,
  type Revisao,
} from "../../data/api/transformometroApi";
import type { ParsedTransformometroRoute } from "../../utils/routeParser";
import { InstanciaDetailPage } from "../pages/InstanciaDetailPage";
import { ProcessoDetailPage } from "../pages/ProcessoDetailPage";
import { RevisaoDetailPage } from "../pages/RevisaoDetailPage";
import { ProcessoWorkspacePanel } from "../processos/ProcessoWorkspacePanel";
import {
  ProcessoWorkspaceShell,
  useProcessoWorkspaceSection,
} from "../processos/ProcessoWorkspaceShell";
import {
  resolveActiveWorkspaceNodeId,
  resolveWorkspacePanelKey,
} from "../processos/processoWorkspaceNav";

type Props = Pick<AppProps, "getAccessToken"> & {
  route: ParsedTransformometroRoute & { processoId: string };
  pathname?: string;
  onNavigate: (path: string) => void;
  onBack: () => void;
};

function panelViewFromKey(panelKey: string): "processo" | "instancia" | "revisao" {
  if (panelKey.startsWith("revisao:")) return "revisao";
  if (panelKey.startsWith("instancia:")) return "instancia";
  return "processo";
}

function panelInstanciaId(panelKey: string): string | undefined {
  if (!panelKey.startsWith("instancia:")) return undefined;
  return panelKey.slice("instancia:".length);
}

function panelRevisaoId(panelKey: string): string | undefined {
  if (!panelKey.startsWith("revisao:")) return undefined;
  return panelKey.slice("revisao:".length);
}

export function ProcessoWorkspacePage({
  getAccessToken,
  route,
  pathname,
  onNavigate,
  onBack,
}: Props) {
  const processoId = route.processoId;
  const activeSection = useProcessoWorkspaceSection();

  const activePanelKey = useMemo(
    () =>
      resolveWorkspacePanelKey({
        view: route.view as "processo" | "instancia" | "revisao",
        instanciaId: route.instanciaId,
        revisaoId: route.revisaoId,
      }),
    [route.instanciaId, route.revisaoId, route.view]
  );

  const activeNodeId = useMemo(() => {
    if (route.view === "revisao" && route.revisaoId) {
      return resolveActiveWorkspaceNodeId({
        view: "revisao",
        revisaoId: route.revisaoId,
        instanciaId: route.instanciaId,
      });
    }
    if (route.view === "instancia" && route.instanciaId) {
      return resolveActiveWorkspaceNodeId({ view: "instancia", instanciaId: route.instanciaId });
    }
    return resolveActiveWorkspaceNodeId({ view: "processo", section: activeSection });
  }, [activeSection, route.instanciaId, route.revisaoId, route.view]);

  const [mountedPanels, setMountedPanels] = useState<Set<string>>(() => new Set([activePanelKey]));
  const [processo, setProcesso] = useState<Processo | null>(null);
  const [instancias, setInstancias] = useState<ProcessoInstancia[]>([]);
  const [revisoes, setRevisoes] = useState<Revisao[]>([]);

  useEffect(() => {
    setMountedPanels((current) => {
      if (current.has(activePanelKey)) return current;
      const next = new Set(current);
      next.add(activePanelKey);
      return next;
    });
  }, [activePanelKey]);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const [proc, inst, revs] = await Promise.all([
          fetchProcesso(processoId, getAccessToken),
          fetchProcessoInstancias(processoId, getAccessToken),
          fetchRevisoes(processoId, getAccessToken),
        ]);
        if (cancelled) return;
        setProcesso(proc);
        setInstancias(inst.items);
        setRevisoes(revs.items);
      } catch {
        if (!cancelled) setProcesso(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [getAccessToken, processoId]);

  const visiblePanels = useMemo(() => {
    const next = new Set(mountedPanels);
    next.add(activePanelKey);
    return next;
  }, [activePanelKey, mountedPanels]);

  function renderPanel(panelKey: string) {
    const view = panelViewFromKey(panelKey);
    const instanciaId = panelInstanciaId(panelKey) ?? route.instanciaId ?? "";
    const revisaoId = panelRevisaoId(panelKey) ?? route.revisaoId ?? "";

    if (view === "processo") {
      return (
        <ProcessoDetailPage
          embedded
          getAccessToken={getAccessToken}
          processoId={processoId}
          pathname={pathname ?? `${TRANSFORMOMETRO_ROUTES.processos}/${processoId}`}
          onNavigate={onNavigate}
          onBack={onBack}
        />
      );
    }

    if (view === "instancia" && instanciaId) {
      return (
        <InstanciaDetailPage
          embedded
          getAccessToken={getAccessToken}
          processoId={processoId}
          instanciaId={instanciaId}
          pathname={pathname ?? `${TRANSFORMOMETRO_ROUTES.processos}/${processoId}/instancias/${instanciaId}`}
          onNavigate={onNavigate}
        />
      );
    }

    if (view === "revisao" && revisaoId) {
      return (
        <RevisaoDetailPage
          embedded
          getAccessToken={getAccessToken}
          processoId={processoId}
          instanciaId={instanciaId}
          revisaoId={revisaoId}
          legacyRevisaoPath={route.legacyRevisaoPath}
          pathname={
            pathname ??
            `${TRANSFORMOMETRO_ROUTES.processos}/${processoId}/instancias/${instanciaId}/revisoes/${revisaoId}`
          }
          onNavigate={onNavigate}
        />
      );
    }

    return null;
  }

  return (
    <TransformometroShell>
      <ProcessoWorkspaceShell
        processoId={processoId}
        activeNodeId={activeNodeId}
        getAccessToken={getAccessToken}
        onNavigate={onNavigate}
        processo={processo}
        instancias={instancias}
        revisoes={revisoes}
      >
        {Array.from(visiblePanels).map((panelKey) => (
          <ProcessoWorkspacePanel
            key={panelKey}
            panelId={panelKey}
            active={panelKey === activePanelKey}
          >
            {renderPanel(panelKey)}
          </ProcessoWorkspacePanel>
        ))}
      </ProcessoWorkspaceShell>
    </TransformometroShell>
  );
}

export function isProcessoWorkspaceRoute(route: ParsedTransformometroRoute): route is ParsedTransformometroRoute & {
  processoId: string;
  view: "processo" | "instancia" | "revisao";
} {
  if (!route.processoId) return false;
  return route.view === "processo" || route.view === "instancia" || route.view === "revisao";
}
