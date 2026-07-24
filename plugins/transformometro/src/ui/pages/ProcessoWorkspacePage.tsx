import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ArrowLeft, Copy, Trash2 } from "lucide-react";

import type { AppProps } from "../../App";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import { TransformometroShell } from "../../components/TransformometroShell";
import { TRANSFORMOMETRO_ROUTES } from "../../constants/routes";
import {
  deleteProcesso,
  duplicateProcesso,
  fetchProcesso,
  fetchProcessoInstancias,
  fetchRevisoes,
  type Processo,
  type ProcessoInstancia,
  type Revisao,
} from "../../data/api/transformometroApi";
import { subscribeWorkspaceTreeRefresh } from "../../utils/navigation";
import { buildProcessoPath } from "../../utils/routeParser";
import type { ParsedTransformometroRoute } from "../../utils/routeParser";
import { useTransformometroEntityWatch } from "../../hooks/useTransformometroEntityWatch";
import { useTransformometroCatalogWatch } from "../../hooks/useTransformometroCatalogWatch";
import { InstanciaDetailPage } from "../pages/InstanciaDetailPage";
import { ProcessoDetailPage } from "../pages/ProcessoDetailPage";
import { RevisaoDetailPage } from "../pages/RevisaoDetailPage";
import { ProcessoWorkspacePanel } from "../processos/ProcessoWorkspacePanel";
import {
  ProcessoWorkspaceShell,
  useInstanciaWorkspaceSection,
  useProcessoWorkspaceSection,
  useRevisaoWorkspaceSection,
} from "../processos/ProcessoWorkspaceShell";
import { DS_GHOST_BTN, dsGhostBtn } from "../../components/ghostChrome";
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
  const confirm = useConfirm();
  const processoId = route.processoId;
  const activeSection = useProcessoWorkspaceSection();
  const activeInstanciaSection = useInstanciaWorkspaceSection();
  const [mountedPanels, setMountedPanels] = useState<Set<string>>(() => new Set());
  const [processo, setProcesso] = useState<Processo | null>(null);
  const [instancias, setInstancias] = useState<ProcessoInstancia[]>([]);
  const [revisoes, setRevisoes] = useState<Revisao[]>([]);
  const missingRevisaoRefreshKey = useRef<string | null>(null);

  const reloadWorkspaceTree = useCallback(async () => {
    try {
      const [proc, inst, revs] = await Promise.all([
        fetchProcesso(processoId, getAccessToken),
        fetchProcessoInstancias(processoId, getAccessToken),
        fetchRevisoes(processoId, getAccessToken),
      ]);
      setProcesso(proc);
      setInstancias(inst.items);
      setRevisoes(revs.items);
    } catch {
      setProcesso(null);
    }
  }, [getAccessToken, processoId]);

  const activeRevisao = useMemo(
    () => revisoes.find((row) => row.revisao_id === route.revisaoId) ?? null,
    [revisoes, route.revisaoId]
  );
  const activeRevisaoSection = useRevisaoWorkspaceSection(activeRevisao?.cenario_tipo);

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
        revisaoSection: activeRevisaoSection,
      });
    }
    if (route.view === "instancia" && route.instanciaId) {
      return resolveActiveWorkspaceNodeId({
        view: "instancia",
        instanciaId: route.instanciaId,
        instanciaSection: activeInstanciaSection,
      });
    }
    return resolveActiveWorkspaceNodeId({ view: "processo", section: activeSection });
  }, [
    activeInstanciaSection,
    activeRevisaoSection,
    activeSection,
    route.instanciaId,
    route.revisaoId,
    route.view,
  ]);

  useEffect(() => {
    setMountedPanels((current) => {
      if (current.has(activePanelKey)) return current;
      const next = new Set(current);
      next.add(activePanelKey);
      return next;
    });
  }, [activePanelKey]);

  useEffect(() => {
    void reloadWorkspaceTree();
  }, [reloadWorkspaceTree]);

  useEffect(() => {
    return subscribeWorkspaceTreeRefresh(() => {
      missingRevisaoRefreshKey.current = null;
      void reloadWorkspaceTree();
    });
  }, [reloadWorkspaceTree]);

  // Tempo real: create/update/delete de melhoria/revisão (fan-out na sala do processo).
  useTransformometroEntityWatch({
    entities: [{ entityType: "processo", entityId: processoId }],
    getAccessToken,
    enabled: Boolean(processoId),
    onEntityUpdated: () => {
      missingRevisaoRefreshKey.current = null;
      void reloadWorkspaceTree();
    },
  });

  // Import JSON / mutações de catálogo: árvore também escuta catalog:processo.
  useTransformometroCatalogWatch({
    catalogId: "processo",
    getAccessToken,
    enabled: Boolean(processoId),
    onUpdated: () => {
      missingRevisaoRefreshKey.current = null;
      void reloadWorkspaceTree();
    },
  });

  // Self-heal: revisão aberta na URL ainda não está na árvore (ex.: criada/duplicada sem refresh).
  useEffect(() => {
    if (route.view !== "revisao" || !route.revisaoId) return;
    if (revisoes.some((row) => row.revisao_id === route.revisaoId)) {
      missingRevisaoRefreshKey.current = null;
      return;
    }
    if (missingRevisaoRefreshKey.current === route.revisaoId) return;
    missingRevisaoRefreshKey.current = route.revisaoId;
    void reloadWorkspaceTree();
  }, [reloadWorkspaceTree, revisoes, route.revisaoId, route.view]);

  const visiblePanels = useMemo(() => {
    const next = new Set(mountedPanels);
    next.add(activePanelKey);
    return next;
  }, [activePanelKey, mountedPanels]);

  async function handleDuplicateProcesso() {
    if (!processo) return;
    const label = `${processo.codigo_processo} — ${processo.nome_processo}`;
    const confirmed = await confirm({
      title: "Duplicar processo",
      message: `Duplicar ${label}? Serão copiados diagrama, mapeamento WBS, melhorias, revisões, medições, investimentos, vínculos e evidências.`,
      confirmLabel: "Duplicar",
    });
    if (!confirmed) return;
    try {
      const result = await duplicateProcesso(processoId, undefined, getAccessToken);
      onNavigate(buildProcessoPath(result.processo.processo_id));
    } catch {
      // erro exibido pelo painel ativo via StatusAlerts
    }
  }

  async function handleDeleteProcesso() {
    if (!processo) return;
    const label = `${processo.codigo_processo} — ${processo.nome_processo}`;
    const confirmed = await confirm({
      title: "Excluir processo",
      message: `Excluir o processo-mestre ${label} e todo o cadastro associado (melhorias, revisões, medições)? Esta ação é uma exclusão lógica. Você será redirecionado à lista.`,
      confirmLabel: "Excluir processo",
      variant: "danger",
    });
    if (!confirmed) return;
    try {
      await deleteProcesso(processoId, getAccessToken);
      onBack();
    } catch {
      // erro exibido pelo painel ativo via StatusAlerts
    }
  }

  const processBackAction = (
    <button type="button" className={`${DS_GHOST_BTN} tm-processo-workspace-sidebar__action-btn`} onClick={onBack}>
      <ArrowLeft size={16} />
      Lista
    </button>
  );

  const processSidebarActions = (
    <>
      <button
        type="button"
        className={`${DS_GHOST_BTN} tm-processo-workspace-sidebar__action-btn`}
        disabled={!processo}
        onClick={() => void handleDuplicateProcesso()}
      >
        <Copy size={16} />
        Duplicar processo
      </button>
      <button
        type="button"
        className={`${dsGhostBtn('danger')} tm-processo-workspace-sidebar__action-btn`}
        disabled={!processo}
        onClick={() => void handleDeleteProcesso()}
      >
        <Trash2 size={16} />
        Excluir processo
      </button>
    </>
  );

  function renderPanel(panelKey: string) {
    const isActive = panelKey === activePanelKey;
    const view = panelViewFromKey(panelKey);
    const instanciaId = panelInstanciaId(panelKey) ?? route.instanciaId ?? "";
    const revisaoId = panelRevisaoId(panelKey) ?? route.revisaoId ?? "";

    if (view === "processo") {
      return (
        <ProcessoDetailPage
          embedded
          embeddedActive={isActive}
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
          embeddedActive={isActive}
          activeSection={activeInstanciaSection}
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
          embeddedActive={isActive}
          activeSection={activeRevisaoSection}
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
        processActions={route.view === "processo" ? processSidebarActions : undefined}
        backActions={processBackAction}
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
