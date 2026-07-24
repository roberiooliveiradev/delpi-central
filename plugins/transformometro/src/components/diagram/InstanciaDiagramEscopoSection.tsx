import { useCallback, useEffect, useState } from "react";

import type { AppProps } from "../../App";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  fetchInstanciaDiagramEscopo,
  fetchProcessoDiagrama,
  saveInstanciaDiagramEscopo,
} from "../../data/api/transformometroDiagramApi";
import {
  FieldLabel,
  emptyEscopo,
  emptyFlowchart,
  DiagramFullscreenFrame,
  NativeCheckboxControl,
  useEditableDraft,
  type FlowchartEscopo,
  type FlowchartV1,
} from "@delpi/plugin-ui/index";
import { DirtySaveActions } from "../ui/DirtySaveActions";
import { FlowchartEditor } from "./TransformometroFlowchartEditor";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  instanciaId: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  resyncVersion?: number;
  onError: (message: string | null) => void;
  /** Após salvar — invalida diagrama composto do processo (keep-alive). */
  onSaved?: () => void;
};

export function InstanciaDiagramEscopoSection({
  processoId,
  instanciaId,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  resyncVersion = 0,
  onError,
  onSaved,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [macro, setMacro] = useState<FlowchartV1>(emptyFlowchart());
  const { value: escopo, setValue, dirty, replace } = useEditableDraft<FlowchartEscopo>(emptyEscopo());

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
      replace({
        node_ids: escopoData.node_ids ?? [],
        inherit_all: escopoData.inherit_all ?? true,
        include_boundary_edges: escopoData.include_boundary_edges ?? false,
      });
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar escopo do diagrama.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, instanciaId, onError, processoId, replace]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!resyncVersion) return;
    void load();
  }, [resyncVersion, load]);

  function toggleScopeNode(nodeId: string) {
    if (readOnly) return;
    setValue((current) => {
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
      onSaved?.();
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

      <NativeCheckboxControl
        className="tm-diagram-section__checkbox"
        checked={escopo.inherit_all}
        disabled={readOnly}
        onChange={(inherit_all) =>
          setValue((current) => ({
            ...current,
            inherit_all,
            node_ids: inherit_all ? [] : macro.nodes.map((node) => node.id),
          }))
        }
        label="Usar diagrama macro completo nesta instância"
        hint={TM_HELP_TOOLTIPS.instancias.diagramaEscopoMacroCompleto}
      />

      <NativeCheckboxControl
        className="tm-diagram-section__checkbox"
        checked={Boolean(escopo.include_boundary_edges)}
        disabled={readOnly || escopo.inherit_all}
        onChange={(include_boundary_edges) =>
          setValue((current) => ({ ...current, include_boundary_edges }))
        }
        label="Incluir arestas na fronteira do escopo"
        hint={TM_HELP_TOOLTIPS.instancias.diagramaEscopoArestasFronteira}
      />

      <DiagramFullscreenFrame
        title="Escopo no diagrama"
        subtitle={
          escopo.inherit_all
            ? "Macro completo: todas as etapas desta melhoria. Desmarque a opção acima para selecionar um subset no desenho."
            : "Clique nos nós para incluir ou excluir do escopo. Arestas de fronteira seguem a opção acima."
        }
        portalScopeClassName="dashboard-transformometro"
        labels={{ expandHint: TM_HELP_TOOLTIPS.diagramEditor.fullscreen }}
      >
        <FlowchartEditor
          value={macro}
          readOnly
          selectedScopeIds={selectedScopeIds}
          onToggleScopeNode={readOnly ? undefined : toggleScopeNode}
          showTemplates={false}
          showPreviewTab={false}
        />

        {!readOnly ? (
          <DirtySaveActions
            dirty={dirty}
            saving={saving}
            label="Salvar escopo"
            onSave={() => void handleSave()}
          />
        ) : null}
      </DiagramFullscreenFrame>
    </div>
  );
}
