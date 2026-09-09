import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Panel,
  Position,
  ReactFlow,
  ReactFlowProvider,
  applyEdgeChanges,
  applyNodeChanges,
  type Connection,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { useDelpiDarkMode } from "@delpi/plugin-ui/index";
import { Cpu, FileCode, MoreHorizontal } from "lucide-react";
import { memo, useCallback, useEffect, useMemo, useState, type ReactNode } from "react";

import { putDeviceFirmwareLink } from "../api/productionPulseApi";
import { PpStateBox } from "../app/productionPulseUi";
import type { DeviceListItem } from "../types/device";
import {
  buildFirmwareLinkGraph,
  type FirmwareFamilyNode,
  type FirmwareLinkGraphEdge,
} from "../utils/firmwareLinkGraph";

/** Show MiniMap only when the graph is large enough to need overview. */
export const ADMIN_HUB_MINIMAP_NODE_THRESHOLD = 8;

export type CanvasEntitySelection =
  | { type: "device"; id: string; nodeId: string }
  | { type: "firmware"; id: string; nodeId: string; firmwareKey: string };

type FirmwareNodeData = {
  label: string;
  subtitle?: string;
  firmwareKey: string;
  firmwareId?: string | null;
  latestVersion?: string | null;
  linkedCount?: number;
  outdatedCount?: number;
  dimmed?: boolean;
  canManage: boolean;
  onOpenMenu?: (payload: { firmwareKey: string; firmwareId?: string | null; nodeId: string }) => void;
  onSelect?: (payload: { firmwareKey: string; firmwareId?: string | null; nodeId: string }) => void;
};

type DeviceNodeData = {
  label: string;
  subtitle?: string;
  deviceId: string;
  linked: boolean;
  dimmed?: boolean;
  status?: string | null;
  counter?: number | null;
  counterDay?: number | null;
  counterShift?: number | null;
  installedFirmwareVersion?: string | null;
  availableVersion?: string | null;
  canManage: boolean;
  onOpenMenu?: (payload: { deviceId: string; nodeId: string }) => void;
  onSelect?: (payload: { deviceId: string; nodeId: string }) => void;
};

function statusDotClass(status: string | null | undefined): string {
  if (status === "online") return "pp-node-status pp-node-status--online";
  if (status === "offline") return "pp-node-status pp-node-status--offline";
  if (status === "disabled") return "pp-node-status pp-node-status--disabled";
  return "pp-node-status";
}

function statusLabel(status: string | null | undefined): string {
  if (status === "online") return "Online";
  if (status === "offline") return "Offline";
  if (status === "disabled") return "Inativo";
  if (status === "no_binding") return "Sem vínculo";
  return "—";
}

function FirmwareNodeView({ id, data }: NodeProps<Node<FirmwareNodeData>>) {
  const outdated = (data.outdatedCount ?? 0) > 0;
  return (
    <div
      className={`pp-firmware-node pp-map-node--compact${data.dimmed ? " pp-map-node--dimmed" : ""}`}
      data-entity="firmware"
      onClick={() =>
        data.onSelect?.({
          firmwareKey: data.firmwareKey,
          firmwareId: data.firmwareId,
          nodeId: id,
        })
      }
    >
      <div className="pp-map-node__head nodrag nopan">
        <span className="pp-map-node__kind" aria-hidden="true">
          <FileCode size={14} strokeWidth={2} />
        </span>
        <strong className="pp-map-node__title">{data.label}</strong>
        <button
          type="button"
          className="pp-map-node__menu"
          aria-label="Ações do firmware"
          aria-haspopup="menu"
          onClick={(event) => {
            event.stopPropagation();
            data.onOpenMenu?.({
              firmwareKey: data.firmwareKey,
              firmwareId: data.firmwareId,
              nodeId: id,
            });
          }}
        >
          <MoreHorizontal size={16} aria-hidden="true" />
        </button>
      </div>
      <div className="pp-map-node__metrics pp-map-node__metrics--compact">
        <div>v{data.latestVersion ?? "—"}</div>
        <div>
          {data.linkedCount ?? 0} IoT
          {outdated ? ` · ${data.outdatedCount} desatul.` : ""}
        </div>
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

function DeviceNodeView({ id, data }: NodeProps<Node<DeviceNodeData>>) {
  const outdated =
    Boolean(data.availableVersion) &&
    Boolean(data.installedFirmwareVersion) &&
    data.availableVersion !== data.installedFirmwareVersion;
  return (
    <div
      className={`pp-device-node pp-map-node--compact${data.linked ? " pp-device-node--linked" : ""}${
        data.dimmed ? " pp-map-node--dimmed" : ""
      }`}
      data-entity="device"
      data-outdated={outdated ? "true" : undefined}
      onClick={() => data.onSelect?.({ deviceId: data.deviceId, nodeId: id })}
    >
      <Handle type="target" position={Position.Left} />
      <div className="pp-map-node__head nodrag nopan">
        <span className="pp-map-node__kind" aria-hidden="true">
          <Cpu size={14} strokeWidth={2} />
        </span>
        <strong className="pp-map-node__title">{data.label}</strong>
        <button
          type="button"
          className="pp-map-node__menu"
          aria-label="Ações do IoT"
          aria-haspopup="menu"
          onClick={(event) => {
            event.stopPropagation();
            data.onOpenMenu?.({ deviceId: data.deviceId, nodeId: id });
          }}
        >
          <MoreHorizontal size={16} aria-hidden="true" />
        </button>
      </div>
      <div className="pp-map-node__status-row">
        <span className={statusDotClass(data.status)} aria-hidden="true" />
        <span>{statusLabel(data.status)}</span>
        {data.counter != null ? (
          <span className="pp-map-node__metric-strong">{data.counter}</span>
        ) : null}
      </div>
      <div className="pp-map-node__metrics pp-map-node__metrics--compact">
        <div>
          FW {data.installedFirmwareVersion ?? "—"}
          {outdated ? " · desatul." : ""}
        </div>
      </div>
    </div>
  );
}

const nodeTypes = {
  firmware: memo(FirmwareNodeView),
  device: memo(DeviceNodeView),
};

export type FirmwareDeviceLinkCanvasProps = {
  families: FirmwareFamilyNode[];
  devices: DeviceListItem[];
  canManage: boolean;
  filterQuery?: string;
  filterStatus?: string;
  onLinked: () => void;
  onUnlink?: (deviceId: string) => void | Promise<void>;
  onUpdateDevice?: (deviceId: string) => void | Promise<void>;
  onUpdateFamily?: (firmwareKey: string) => void | Promise<void>;
  onSelectEntity?: (selection: CanvasEntitySelection) => void;
  onOpenDeviceMenu?: (payload: { deviceId: string; nodeId: string }) => void;
  onOpenFirmwareMenu?: (payload: {
    firmwareKey: string;
    firmwareId?: string | null;
    nodeId: string;
  }) => void;
  onNodeDragStart?: () => void;
  overlayTopLeft?: ReactNode;
  overlayTopRight?: ReactNode;
  overlayBottom?: ReactNode;
  nodesLocked?: boolean;
  /** Override MiniMap visibility; default uses ADMIN_HUB_MINIMAP_NODE_THRESHOLD. */
  showMiniMap?: boolean;
};

function toFlowEdges(edges: FirmwareLinkGraphEdge[], canManage: boolean): Edge[] {
  return edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    animated: edge.kind === "inherited",
    style:
      edge.kind === "inherited"
        ? { strokeDasharray: "6 4", stroke: "var(--pp-text-muted)" }
        : { stroke: "var(--pp-accent)" },
    markerEnd: { type: MarkerType.ArrowClosed },
    deletable: canManage && edge.kind === "explicit",
    data: { kind: edge.kind },
  }));
}

function FirmwareDeviceLinkCanvasInner({
  families,
  devices,
  canManage,
  filterQuery,
  filterStatus,
  onLinked,
  onUnlink,
  onUpdateDevice,
  onUpdateFamily,
  onSelectEntity,
  onOpenDeviceMenu,
  onOpenFirmwareMenu,
  onNodeDragStart,
  overlayTopLeft,
  overlayTopRight,
  overlayBottom,
  nodesLocked = false,
  showMiniMap,
}: FirmwareDeviceLinkCanvasProps) {
  void onUpdateDevice;
  void onUpdateFamily;
  const isDark = useDelpiDarkMode();
  const colorMode = isDark ? "dark" : "light";
  const graph = useMemo(
    () =>
      buildFirmwareLinkGraph({
        families,
        devices,
        filterQuery,
        filterStatus,
      }),
    [families, devices, filterQuery, filterStatus],
  );

  const miniMapVisible =
    showMiniMap ?? graph.nodes.length >= ADMIN_HUB_MINIMAP_NODE_THRESHOLD;

  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const linkedDeviceIds = new Set(
      graph.edges.filter((e) => e.kind === "explicit").map((e) => e.target),
    );
    const familyIdByKey = new Map(
      families.map((family) => [family.firmwareKey, family.latestFirmwareId ?? null]),
    );
    setNodes(
      graph.nodes.map((n) => {
        if (n.kind === "firmware") {
          return {
            id: n.id,
            type: "firmware",
            position: n.position,
            className: n.dimmed ? "pp-flow-node--dimmed" : undefined,
            data: {
              label: n.label,
              subtitle: n.subtitle,
              firmwareKey: n.firmwareKey!,
              firmwareId: familyIdByKey.get(n.firmwareKey!) ?? null,
              latestVersion: n.latestVersion,
              linkedCount: n.linkedCount,
              outdatedCount: n.outdatedCount,
              dimmed: n.dimmed,
              canManage,
              onOpenMenu: onOpenFirmwareMenu,
              onSelect: (payload) => {
                onSelectEntity?.({
                  type: "firmware",
                  id: payload.firmwareId || payload.firmwareKey,
                  nodeId: payload.nodeId,
                  firmwareKey: payload.firmwareKey,
                });
              },
            },
          } satisfies Node<FirmwareNodeData>;
        }
        return {
          id: n.id,
          type: "device",
          position: n.position,
          className: n.dimmed ? "pp-flow-node--dimmed" : undefined,
          data: {
            label: n.label,
            subtitle: n.subtitle,
            deviceId: n.deviceId!,
            linked: linkedDeviceIds.has(n.id),
            dimmed: n.dimmed,
            status: n.status,
            counter: n.counter,
            counterDay: n.counterDay,
            counterShift: n.counterShift,
            installedFirmwareVersion: n.installedFirmwareVersion,
            availableVersion: n.availableVersion,
            canManage,
            onOpenMenu: onOpenDeviceMenu,
            onSelect: (payload) => {
              onSelectEntity?.({
                type: "device",
                id: payload.deviceId,
                nodeId: payload.nodeId,
              });
            },
          },
        } satisfies Node<DeviceNodeData>;
      }),
    );
    setEdges(toFlowEdges(graph.edges, canManage));
    setError(null);
  }, [
    graph,
    families,
    canManage,
    onSelectEntity,
    onOpenDeviceMenu,
    onOpenFirmwareMenu,
  ]);

  const onNodesChange = useCallback((changes: NodeChange[]) => {
    setNodes((current) => applyNodeChanges(changes, current));
  }, []);

  const onEdgesChange = useCallback((changes: EdgeChange[]) => {
    setEdges((current) => applyEdgeChanges(changes, current));
  }, []);

  const onConnect = useCallback(
    async (connection: Connection) => {
      if (!canManage || busy) return;
      const source = connection.source;
      const target = connection.target;
      if (!source?.startsWith("fw:") || !target?.startsWith("dev:")) {
        setError("Conecte do firmware para o IoT.");
        return;
      }
      const firmwareKey = source.slice(3);
      const deviceId = target.slice(4);
      setBusy(true);
      setError(null);
      try {
        await putDeviceFirmwareLink(deviceId, firmwareKey);
        onLinked();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao vincular.");
      } finally {
        setBusy(false);
      }
    },
    [busy, canManage, onLinked],
  );

  const unlinkDevice = useCallback(
    async (deviceId: string) => {
      if (onUnlink) {
        await onUnlink(deviceId);
        return;
      }
      await putDeviceFirmwareLink(deviceId, null);
      onLinked();
    },
    [onLinked, onUnlink],
  );

  const onEdgesDelete = useCallback(
    async (deleted: Edge[]) => {
      if (!canManage || busy) return;
      const explicit = deleted.filter((edge) => edge.data?.kind === "explicit");
      if (explicit.length === 0) return;
      setBusy(true);
      setError(null);
      try {
        for (const edge of explicit) {
          const deviceId = String(edge.target).replace(/^dev:/, "");
          await unlinkDevice(deviceId);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao desvincular.");
        onLinked();
      } finally {
        setBusy(false);
      }
    },
    [busy, canManage, onLinked, unlinkDevice],
  );

  if (families.length === 0 && devices.length === 0) {
    return (
      <PpStateBox
        variant="empty"
        title="Sem nós"
        message="Publique um firmware e cadastre IoTs nesta filial."
      />
    );
  }

  return (
    <div className="pp-firmware-link-canvas-wrap pp-firmware-link-canvas-wrap--fill" data-color-mode={colorMode}>
      {error ? <PpStateBox variant="error" title="Conexão" message={error} /> : null}
      <div className="pp-firmware-link-canvas pp-firmware-link-canvas--fill">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          colorMode={colorMode}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={(c) => void onConnect(c)}
          onEdgesDelete={(e) => void onEdgesDelete(e)}
          onNodeDragStart={() => onNodeDragStart?.()}
          deleteKeyCode={["Backspace", "Delete"]}
          nodesDraggable={!nodesLocked}
          nodesConnectable={canManage && !busy}
          nodesFocusable
          edgesFocusable
          autoPanOnNodeFocus
          edgesReconnectable={false}
          fitView
          minZoom={0.35}
          maxZoom={1.75}
          panOnScroll
          proOptions={{ hideAttribution: true }}
          aria-label="Canvas de vínculos entre firmwares e dispositivos IoT"
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={18}
            size={1}
            color={isDark ? "rgba(148, 163, 184, 0.28)" : "rgba(100, 116, 139, 0.35)"}
          />
          {overlayTopLeft ? (
            <Panel position="top-left" className="pp-map-overlay-panel">
              {overlayTopLeft}
            </Panel>
          ) : null}
          {overlayTopRight ? (
            <Panel position="top-right" className="pp-map-overlay-panel">
              {overlayTopRight}
            </Panel>
          ) : null}
          {overlayBottom ? (
            <Panel position="bottom-center" className="pp-map-overlay-panel pp-map-overlay-panel--bottom">
              {overlayBottom}
            </Panel>
          ) : null}
          <Controls showInteractive={false} position="bottom-left" />
          {miniMapVisible ? (
            <MiniMap
              position="bottom-right"
              pannable
              zoomable
              ariaLabel="Miniatura do mapa Admin"
            />
          ) : null}
        </ReactFlow>
      </div>
    </div>
  );
}

export function FirmwareDeviceLinkCanvas(props: FirmwareDeviceLinkCanvasProps) {
  return (
    <ReactFlowProvider>
      <FirmwareDeviceLinkCanvasInner {...props} />
    </ReactFlowProvider>
  );
}
