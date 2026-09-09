import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MarkerType,
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
import { memo, useCallback, useEffect, useMemo, useState } from "react";

import { putDeviceFirmwareLink } from "../api/productionPulseApi";
import { PpActionButton, PpStateBox } from "../app/productionPulseUi";
import { PP_HELP } from "../content/helpTooltips";
import type { DeviceListItem } from "../types/device";
import {
  buildFirmwareLinkGraph,
  type FirmwareFamilyNode,
  type FirmwareLinkGraphEdge,
} from "../utils/firmwareLinkGraph";

type FirmwareNodeData = {
  label: string;
  subtitle?: string;
  firmwareKey: string;
  latestVersion?: string | null;
  linkedCount?: number;
  canManage: boolean;
  onUpdateFamily?: (firmwareKey: string) => void;
};

type DeviceNodeData = {
  label: string;
  subtitle?: string;
  deviceId: string;
  linked: boolean;
  canManage: boolean;
  onUnlink?: (deviceId: string) => void;
  onUpdateDevice?: (deviceId: string) => void;
  onSelectDevice?: (deviceId: string) => void;
};

function FirmwareNodeView({ data }: NodeProps<Node<FirmwareNodeData>>) {
  return (
    <div className="pp-firmware-node">
      <strong>{data.label}</strong>
      {data.subtitle ? <div className="pp-firmware-node__meta">{data.subtitle}</div> : null}
      {data.canManage && data.onUpdateFamily ? (
        <div className="pp-firmware-node__actions nodrag nopan">
          <PpActionButton
            variant="ghost"
            className="nodrag"
            onClick={() => data.onUpdateFamily?.(data.firmwareKey)}
          >
            Atualizar ligados
          </PpActionButton>
        </div>
      ) : null}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

function DeviceNodeView({ data }: NodeProps<Node<DeviceNodeData>>) {
  return (
    <div className={`pp-device-node${data.linked ? " pp-device-node--linked" : ""}`}>
      <Handle type="target" position={Position.Left} />
      <strong>{data.label}</strong>
      {data.subtitle ? <div className="pp-device-node__meta">{data.subtitle}</div> : null}
      <div className="pp-firmware-node__actions nodrag nopan">
        {data.canManage && data.linked && data.onUnlink ? (
          <PpActionButton
            variant="ghost"
            className="nodrag"
            onClick={() => data.onUnlink?.(data.deviceId)}
            title={PP_HELP.otaLinks.disconnect}
          >
            Desvincular
          </PpActionButton>
        ) : null}
        {data.canManage && data.onUpdateDevice ? (
          <PpActionButton
            variant="ghost"
            className="nodrag"
            onClick={() => data.onUpdateDevice?.(data.deviceId)}
          >
            Atualizar este
          </PpActionButton>
        ) : null}
        {data.onSelectDevice ? (
          <PpActionButton
            variant="ghost"
            className="nodrag"
            onClick={() => data.onSelectDevice?.(data.deviceId)}
          >
            Abrir detalhe
          </PpActionButton>
        ) : null}
      </div>
    </div>
  );
}

const nodeTypes = {
  firmware: memo(FirmwareNodeView),
  device: memo(DeviceNodeView),
};

type FirmwareDeviceLinkCanvasProps = {
  families: FirmwareFamilyNode[];
  devices: DeviceListItem[];
  canManage: boolean;
  onLinked: () => void;
  onUnlink?: (deviceId: string) => void | Promise<void>;
  onUpdateDevice?: (deviceId: string) => void | Promise<void>;
  onUpdateFamily?: (firmwareKey: string) => void | Promise<void>;
  onSelectDevice?: (deviceId: string) => void;
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
  onLinked,
  onUnlink,
  onUpdateDevice,
  onUpdateFamily,
  onSelectDevice,
}: FirmwareDeviceLinkCanvasProps) {
  const isDark = useDelpiDarkMode();
  const colorMode = isDark ? "dark" : "light";
  const graph = useMemo(
    () => buildFirmwareLinkGraph({ families, devices }),
    [families, devices],
  );

  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const linkedDeviceIds = new Set(
      graph.edges.filter((e) => e.kind === "explicit").map((e) => e.target),
    );
    setNodes(
      graph.nodes.map((n) => {
        if (n.kind === "firmware") {
          return {
            id: n.id,
            type: "firmware",
            position: n.position,
            data: {
              label: n.label,
              subtitle: n.subtitle,
              firmwareKey: n.firmwareKey!,
              latestVersion: n.latestVersion,
              linkedCount: n.linkedCount,
              canManage,
              onUpdateFamily: onUpdateFamily
                ? (firmwareKey: string) => {
                    void onUpdateFamily(firmwareKey);
                  }
                : undefined,
            },
          } satisfies Node<FirmwareNodeData>;
        }
        return {
          id: n.id,
          type: "device",
          position: n.position,
          data: {
            label: n.label,
            subtitle: n.subtitle,
            deviceId: n.deviceId!,
            linked: linkedDeviceIds.has(n.id),
            canManage,
            onUnlink: onUnlink
              ? (deviceId: string) => {
                  void onUnlink(deviceId);
                }
              : undefined,
            onUpdateDevice: onUpdateDevice
              ? (deviceId: string) => {
                  void onUpdateDevice(deviceId);
                }
              : undefined,
            onSelectDevice,
          },
        } satisfies Node<DeviceNodeData>;
      }),
    );
    setEdges(toFlowEdges(graph.edges, canManage));
    setError(null);
  }, [graph, canManage, onUnlink, onUpdateDevice, onUpdateFamily, onSelectDevice]);

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
    <div className="pp-firmware-link-canvas-wrap" data-color-mode={colorMode}>
      {error ? <PpStateBox variant="error" title="Conexão" message={error} /> : null}
      {!canManage ? (
        <PpStateBox
          variant="empty"
          title="Somente leitura"
          message="Você pode ver as conexões, mas não alterar vínculos."
        />
      ) : (
        <p className="pp-muted">
          Arraste do firmware (esquerda) para o IoT. Cada IoT aceita um firmware; nova seta
          substitui. Delete/Backspace na seta sólida ou use Desvincular. Tracejada = via driver
          (somente leitura).
        </p>
      )}
      <div className="pp-firmware-link-canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          colorMode={colorMode}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={(c) => void onConnect(c)}
          onEdgesDelete={(e) => void onEdgesDelete(e)}
          deleteKeyCode={["Backspace", "Delete"]}
          nodesDraggable
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
          <Controls showInteractive={false} position="bottom-left" />
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
