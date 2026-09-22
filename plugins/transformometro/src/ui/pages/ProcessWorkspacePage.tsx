import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import type { AppProps } from "../../App";
import { useConfirm } from "../../components/ui/ConfirmDialogProvider";
import { TransformometroShell } from "../../components/TransformometroShell";
import { TRANSFORMOMETRO_ROUTES, buildInteractionRoomPath } from "../../constants/routes";
import { openInteractionRoom } from "../../data/api/transformometroInteractionApi";
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
import { InstanceDetailPage } from "../pages/InstanceDetailPage";
import { ProcessDetailPage } from "../pages/ProcessDetailPage";
import { RevisionDetailPage } from "../pages/RevisionDetailPage";
import {
  ProcessWorkspaceChrome,
  type WorkspaceRevisionChromeActions,
} from "../processes/ProcessWorkspaceChrome";
import { ProcessWorkspacePanel } from "../processes/ProcessWorkspacePanel";
import {
  ProcessWorkspaceShell,
  useInstanciaWorkspaceSection,
  useProcessoWorkspaceSection,
  useRevisaoWorkspaceSection,
} from "../processes/ProcessWorkspaceShell";
import { resolveWorkspacePanelKey } from "../processes/processWorkspaceNav";
import { reloadProcessWorkspaceTree } from "../processes/reloadProcessWorkspaceTree";

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

export function ProcessWorkspacePage({
  getAccessToken,
  route,
  pathname,
  onNavigate,
  onBack,
}: Props) {
  const confirm = useConfirm();
  const processoId = route.processoId;
  const [openingRoom, setOpeningRoom] = useState(false);
  const [roomError, setRoomError] = useState<string | null>(null);
  const activeSection = useProcessoWorkspaceSection();
  const activeInstanciaSection = useInstanciaWorkspaceSection();
  const [mountedPanels, setMountedPanels] = useState<Set<string>>(() => new Set());
  const [processo, setProcesso] = useState<Processo | null>(null);
  const [instancias, setInstancias] = useState<ProcessoInstancia[]>([]);
  const [revisoes, setRevisoes] = useState<Revisao[]>([]);
  const [filiaisAtivasCount, setFiliaisAtivasCount] = useState(0);
  const [heroExtras, setHeroExtras] = useState<ReactNode>(null);
  const [revisionActions, setRevisionActions] =
    useState<WorkspaceRevisionChromeActions | null>(null);
  const [treePartialError, setTreePartialError] = useState<string | null>(null);
  const missingRevisaoRefreshKey = useRef<string | null>(null);

  const reloadWorkspaceTree = useCallback(async () => {
    await reloadProcessWorkspaceTree({
      fetchProcesso: () => fetchProcesso(processoId, getAccessToken),
      fetchInstancias: () => fetchProcessoInstancias(processoId, getAccessToken),
      fetchRevisoes: () => fetchRevisoes(processoId, getAccessToken),
      setProcesso: (value) => setProcesso(value as Processo | null),
      setInstancias: (value) => setInstancias(value as ProcessoInstancia[]),
      setRevisoes: (value) => setRevisoes(value as Revisao[]),
      setTreePartialError,
    });
  }, [getAccessToken, processoId]);

  const activeRevisao = useMemo(
    () => revisoes.find((row) => row.revisao_id === route.revisaoId) ?? null,
    [revisoes, route.revisaoId],
  );
  const activeRevisaoSection = useRevisaoWorkspaceSection(activeRevisao?.cenario_tipo);

  const activePanelKey = useMemo(
    () =>
      resolveWorkspacePanelKey({
        view: route.view as "processo" | "instancia" | "revisao",
        instanciaId: route.instanciaId,
        revisaoId: route.revisaoId,
      }),
    [route.instanciaId, route.revisaoId, route.view],
  );

  useEffect(() => {
    setMountedPanels((current) => {
      if (current.has(activePanelKey)) return current;
      const next = new Set(current);
      next.add(activePanelKey);
      return next;
    });
  }, [activePanelKey]);

  useEffect(() => {
    setHeroExtras(null);
    setRevisionActions(null);
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

  useTransformometroEntityWatch({
    entities: [{ entityType: "processo", entityId: processoId }],
    getAccessToken,
    enabled: Boolean(processoId),
    onEntityUpdated: () => {
      missingRevisaoRefreshKey.current = null;
      void reloadWorkspaceTree();
    },
  });

  useTransformometroCatalogWatch({
    catalogId: "processo",
    getAccessToken,
    enabled: Boolean(processoId),
    onUpdated: () => {
      missingRevisaoRefreshKey.current = null;
      void reloadWorkspaceTree();
    },
  });

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

  async function handleOpenInteractionRoom() {
    setOpeningRoom(true);
    setRoomError(null);
    try {
      const room = await openInteractionRoom(processoId, getAccessToken);
      onNavigate(buildInteractionRoomPath(room.id));
    } catch (reason) {
      setRoomError(reason instanceof Error ? reason.message : "Não foi possível abrir a sala.");
    } finally {
      setOpeningRoom(false);
    }
  }

  function renderPanel(panelKey: string) {
    const isActive = panelKey === activePanelKey;
    const view = panelViewFromKey(panelKey);
    const instanciaId = panelInstanciaId(panelKey) ?? route.instanciaId ?? "";
    const revisaoId = panelRevisaoId(panelKey) ?? route.revisaoId ?? "";

    if (view === "processo") {
      return (
        <ProcessDetailPage
          embedded
          embeddedActive={isActive}
          getAccessToken={getAccessToken}
          processoId={processoId}
          pathname={pathname ?? `${TRANSFORMOMETRO_ROUTES.processos}/${processoId}`}
          onNavigate={onNavigate}
          onBack={onBack}
          onHeroExtrasChange={setHeroExtras}
        />
      );
    }

    if (view === "instancia" && instanciaId) {
      return (
        <InstanceDetailPage
          embedded
          embeddedActive={isActive}
          activeSection={activeInstanciaSection}
          getAccessToken={getAccessToken}
          processoId={processoId}
          instanciaId={instanciaId}
          pathname={
            pathname ?? `${TRANSFORMOMETRO_ROUTES.processos}/${processoId}/instancias/${instanciaId}`
          }
          onNavigate={onNavigate}
          onHeroExtrasChange={setHeroExtras}
          onFiliaisAtivasCount={setFiliaisAtivasCount}
        />
      );
    }

    if (view === "revisao" && revisaoId) {
      return (
        <RevisionDetailPage
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
          onHeroExtrasChange={setHeroExtras}
          onRevisionChromeActions={setRevisionActions}
        />
      );
    }

    return null;
  }

  const chrome = (
    <ProcessWorkspaceChrome
      view={route.view as "processo" | "instancia" | "revisao"}
      processo={processo}
      instancias={instancias}
      revisoes={revisoes}
      filiaisAtivasCount={filiaisAtivasCount}
      heroExtras={heroExtras}
      revisionActions={revisionActions}
      processoId={processoId}
      instanciaId={route.instanciaId}
      revisaoId={route.revisaoId}
      activeProcessoSection={activeSection}
      activeInstanciaSection={activeInstanciaSection}
      activeRevisaoSection={activeRevisaoSection}
      onNavigate={onNavigate}
      onBack={onBack}
      onOpenRoom={() => void handleOpenInteractionRoom()}
      openingRoom={openingRoom}
      roomError={roomError}
      treePartialError={treePartialError}
      onDuplicate={() => void handleDuplicateProcesso()}
      onDelete={() => void handleDeleteProcesso()}
    />
  );

  return (
    <TransformometroShell>
      <ProcessWorkspaceShell chrome={chrome}>
        {Array.from(visiblePanels).map((panelKey) => (
          <ProcessWorkspacePanel key={panelKey} panelId={panelKey} active={panelKey === activePanelKey}>
            {renderPanel(panelKey)}
          </ProcessWorkspacePanel>
        ))}
      </ProcessWorkspaceShell>
    </TransformometroShell>
  );
}

export function isProcessWorkspaceRoute(
  route: ParsedTransformometroRoute,
): route is ParsedTransformometroRoute & {
  processoId: string;
  view: "processo" | "instancia" | "revisao";
} {
  if (!route.processoId) return false;
  return route.view === "processo" || route.view === "instancia" || route.view === "revisao";
}
