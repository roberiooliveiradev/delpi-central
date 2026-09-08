import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MarkerType,
  Position,
  ReactFlow,
  ReactFlowProvider,
  applyNodeChanges,
  type Connection,
  type Edge,
  type Node,
  type NodeChange,
  type NodeProps,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { memo, useCallback, useEffect, useMemo, useState } from "react";

import { putDeviceFirmwareLink } from "../api/productionPulseApi";
import { PpStateBox } from "../app/productionPulseUi";
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
};

type DeviceNodeData = {
  label: string;
  subtitle?: string;
  deviceId: string;
  linked: boolean;
};

function FirmwareNodeView({ data }: NodeProps<Node<FirmwareNodeData>>) {
  return (
    <div className="pp-firmware-node">
      <strong>{data.label}</strong>
      {data.subtitle ? <div>{data.subtitle}</div> : null}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

function DeviceNodeView({ data }: NodeProps<Node<DeviceNodeData>>) {
  return (
    <div className={`pp-device-node${data.linked ? " pp-device-node--linked" : ""}`}>
      <Handle type="target" position={Position.Left} />
      <strong>{data.label}</strong>
      {data.subtitle ? <div>{data.subtitle}</div> : null}
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
}: FirmwareDeviceLinkCanvasProps) {
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
          },
        } satisfies Node<DeviceNodeData>;
      }),
    );
    setEdges(toFlowEdges(graph.edges, canManage));
    setError(null);
  }, [graph, canManage]);

  const onNodesChange = useCallback((changes: NodeChange[]) => {
    setNodes((current) => applyNodeChanges(changes, current));
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
          await putDeviceFirmwareLink(deviceId, null);
        }
        onLinked();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Falha ao desvincular.");
        onLinked();
      } finally {
        setBusy(false);
      }
    },
    [busy, canManage, onLinked],
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
    <div className="pp-firmware-link-canvas-wrap">
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
          substitui. Delete na seta sólida desvincula. Tracejada = via driver (somente leitura).
        </p>
      )}
      <div className="pp-firmware-link-canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={() => undefined}
          onConnect={(c) => void onConnect(c)}
          onEdgesDelete={(e) => void onEdgesDelete(e)}
          nodesDraggable
          nodesConnectable={canManage && !busy}
          edgesUpdatable={false}
          fitView
          proOptions={{ hideAttribution: true }}
        >
          <Background variant={BackgroundVariant.Dots} gap={18} size={1} />
          <Controls showInteractive={false} />
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
