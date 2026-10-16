import { useCallback, useEffect, useState } from "react";

import type { AppProps } from "../../../App";
import { TM_HELP_TOOLTIPS } from "../../../content/helpTooltips";
import {
  fetchInstanciaDiagramEscopo,
  fetchProcessoDiagrama,
} from "../../../data/api/transformometroDiagramApi";
import {
  FieldLabel,
  emptyEscopo,
  emptyFlowchart,
  DiagramFullscreenFrame,
  DiagramLayoutProvider,
  NativeCheckboxControl,
  type FlowchartEscopo,
  type FlowchartV1,
} from "@delpi/plugin-ui/index";
import { FlowchartEditor } from "../editor/TransformometroFlowchartEditor";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  instanciaId: string;
  embeddedInCard?: boolean;
  /** `page` = editor full-page (sem modal de tela cheia; layout fill). */
  variant?: "embedded" | "page";
  chromeLeading?: {
    onBack?: () => void;
    backLabel?: string;
    title?: string;
  };
  chromeNotices?: import("react").ReactNode;
  resyncVersion?: number;
  onError: (message: string | null) => void;
};

export function InstanciaDiagramEscopoSection({
  processoId,
  instanciaId,
  getAccessToken,
  embeddedInCard = false,
  variant = "embedded",
  chromeLeading,
  chromeNotices,
  resyncVersion = 0,
  onError,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [macro, setMacro] = useState<FlowchartV1>(emptyFlowchart());
  const [escopo, setEscopo] = useState<FlowchartEscopo>(emptyEscopo());

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

  if (loading) {
    return <p className="ds-hint">Carregando escopo no diagrama…</p>;
  }

  if (!macro.nodes.length) {
    return (
      <p className="ds-hint">
        O processo não possui mapeamento legado. Novos diagramas são BPMN nativos,
        criados no detalhe do processo-mestre.
      </p>
    );
  }

  const canvas = (
    <FlowchartEditor
      value={macro}
      readOnly
      selectedScopeIds={selectedScopeIds}
      showTemplates={false}
      showPreviewTab={false}
      chromeLeading={variant === "page" ? chromeLeading : undefined}
      chromeNotices={variant === "page" ? chromeNotices : undefined}
    />
  );

  return (
    <div
      className={[
        "delpi-ui-bpmn-section",
        variant === "page" ? "delpi-ui-bpmn-section--page" : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {!embeddedInCard && variant !== "page" ? (
        <FieldLabel
          className="tm-field__label"
          label="Escopo no diagrama"
          hint={TM_HELP_TOOLTIPS.instancias.diagramaEscopo}
        />
      ) : null}

      <NativeCheckboxControl
        className="delpi-ui-bpmn-section__checkbox"
        checked={escopo.inherit_all}
        disabled
        onChange={() => undefined}
        label="Usar diagrama macro completo nesta instância"
        hint={TM_HELP_TOOLTIPS.instancias.diagramaEscopoMacroCompleto}
      />

      <NativeCheckboxControl
        className="delpi-ui-bpmn-section__checkbox"
        checked={Boolean(escopo.include_boundary_edges)}
        disabled
        onChange={() => undefined}
        label="Incluir arestas na fronteira do escopo"
        hint={TM_HELP_TOOLTIPS.instancias.diagramaEscopoArestasFronteira}
      />

      {variant === "page" ? (
        <DiagramLayoutProvider layout="fill">
          <div className="delpi-ui-bpmn-workspace delpi-ui-bpmn-workspace--page">
            <div className="delpi-ui-bpmn-workspace__body">{canvas}</div>
          </div>
        </DiagramLayoutProvider>
      ) : (
        <DiagramFullscreenFrame
          title="Escopo no diagrama"
          subtitle={
            escopo.inherit_all
              ? "Escopo legado somente leitura: todas as etapas do macro legado."
              : "Escopo legado somente leitura: subset de etapas do macro legado."
          }
          portalScopeClassName="dashboard-transformometro"
          labels={{ expandHint: TM_HELP_TOOLTIPS.diagramEditor.fullscreen }}
        >
          {canvas}
        </DiagramFullscreenFrame>
      )}
    </div>
  );
}
