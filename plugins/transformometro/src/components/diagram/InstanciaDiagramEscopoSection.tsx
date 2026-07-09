import { lazy, Suspense, useCallback, useEffect, useState } from "react";

import type { AppProps } from "../../App";
import { FieldLabel } from "@delpi/plugin-ui";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  fetchInstanciaDiagramEscopo,
  fetchProcessoDiagrama,
  saveInstanciaDiagramEscopo,
} from "../../data/api/transformometroDiagramApi";
import { emptyEscopo, emptyFlowchart, type FlowchartEscopo, type FlowchartV1 } from "../../types/diagram";
import { DiagramMermaidPreview } from "./DiagramMermaidPreview";
import { DiagramFullscreenFrame } from "./DiagramFullscreenFrame";

const FlowchartEditor = lazy(() =>
  import("./FlowchartEditor").then((module) => ({ default: module.FlowchartEditor }))
);

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  instanciaId: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  resyncVersion?: number;
  onError: (message: string | null) => void;
};

export function InstanciaDiagramEscopoSection({
  processoId,
  instanciaId,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  resyncVersion = 0,
  onError,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [macro, setMacro] = useState<FlowchartV1>(emptyFlowchart());
  const [escopo, setEscopo] = useState<FlowchartEscopo>(emptyEscopo());
  const [mermaid, setMermaid] = useState("");

  const selectedScopeIds = new Set(
    escopo.inherit_all ? macro.nodes.map((node) => node.id) : escopo.node_ids
  );

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const [macroData, escopoData] = await Promise.all([
        fetchProcessoDiagrama(processoId, getAccessToken),
        fetchInstanciaDiagramEscopo(instanciaId, getAccessToken),
      ]);
      setMacro(macroData.conteudo ?? emptyFlowchart());
      setMermaid(macroData.mermaid ?? "");
      setEscopo({
        node_ids: escopoData.node_ids ?? [],
        inherit_all: escopoData.inherit_all ?? true,
        include_boundary_edges: escopoData.include_boundary_edges ?? false,
      });
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar escopo do diagrama.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, instanciaId, onError, processoId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!resyncVersion) return;
    void load();
  }, [resyncVersion, load]);

  function toggleScopeNode(nodeId: string) {
    if (readOnly) return;
    setEscopo((current) => {
      if (current.inherit_all) {
        const allIds = macro.nodes.map((node) => node.id);
        const nextIds = allIds.filter((id) => id !== nodeId);
        return { ...current, inherit_all: false, node_ids: nextIds };
      }
      const has = current.node_ids.includes(nodeId);
      const nextIds = has
        ? current.node_ids.filter((id) => id !== nodeId)
        : [...current.node_ids, nodeId];
      return {
        ...current,
        inherit_all: nextIds.length === macro.nodes.length,
        node_ids: nextIds.length === macro.nodes.length ? [] : nextIds,
      };
    });
  }

  async function handleSave() {
    setSaving(true);
    onError(null);
    try {
      const payload: FlowchartEscopo = escopo.inherit_all
        ? { node_ids: [], inherit_all: true, include_boundary_edges: escopo.include_boundary_edges }
        : escopo;
      await saveInstanciaDiagramEscopo(instanciaId, payload, getAccessToken);
      await load();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar escopo.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="ds-hint">Carregando escopo no diagrama…</p>;
  }

  if (!macro.nodes.length) {
    return (
      <p className="ds-hint">
        O processo ainda não possui diagrama macro. Cadastre o mapa no detalhe do processo-mestre.
      </p>
    );
  }

  return (
    <div className="tm-diagram-section">
      {!embeddedInCard ? (
        <FieldLabel className="tm-field__label" label="Escopo no diagrama" hint={TM_HELP_TOOLTIPS.instancias.diagramaEscopo} />
      ) : null}

      <label className="tm-diagram-section__checkbox">
        <input
          type="checkbox"
          checked={escopo.inherit_all}
          disabled={readOnly}
          onChange={(event) =>
            setEscopo((current) => ({
              ...current,
              inherit_all: event.target.checked,
              node_ids: event.target.checked ? [] : macro.nodes.map((node) => node.id),
            }))
          }
        />
        Usar diagrama macro completo nesta instância
      </label>

      <label className="tm-diagram-section__checkbox">
        <input
          type="checkbox"
          checked={Boolean(escopo.include_boundary_edges)}
          disabled={readOnly || escopo.inherit_all}
          onChange={(event) =>
            setEscopo((current) => ({ ...current, include_boundary_edges: event.target.checked }))
          }
        />
        Incluir arestas na fronteira do escopo
      </label>

      <DiagramFullscreenFrame
        title="Escopo no diagrama"
        subtitle="Selecione os nós do mapa macro que se aplicam a esta instância."
      >
        <Suspense fallback={<p className="ds-hint">Carregando canvas…</p>}>
          <FlowchartEditor
            value={macro}
            readOnly
            selectedScopeIds={selectedScopeIds}
            onToggleScopeNode={readOnly ? undefined : toggleScopeNode}
            showTemplates={false}
            showPreviewTab={false}
          />
        </Suspense>

        {mermaid ? <DiagramMermaidPreview code={mermaid} /> : null}

        {!readOnly ? (
          <div className="tm-diagram-section__actions">
            <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
              {saving ? "Salvando…" : "Salvar escopo"}
            </button>
          </div>
        ) : null}
      </DiagramFullscreenFrame>
    </div>
  );
}
