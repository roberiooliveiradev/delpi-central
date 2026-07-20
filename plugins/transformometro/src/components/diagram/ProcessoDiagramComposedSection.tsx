import { useCallback, useEffect, useMemo, useState } from "react";

import type { AppProps } from "../../App";
import { FieldLabel, NativeTextControl, DiagramMermaidPreview } from "@delpi/plugin-ui/index";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import { fetchProcessoDiagramaComposed } from "../../data/api/transformometroDiagramApi";
import type { ComposedProcessoDiagram } from "../../types/diagram";
import { stripFlowchartHighlights } from "../../utils/diffHighlightDisplay";
import { todayDateInput } from "../../utils/dateInputs";
import { DiffHighlightToggle } from "../DiffHighlightToggle";
import { DS_GHOST_BTN } from "../ghostChrome";
import { FlowchartEditor } from "./TransformometroFlowchartEditor";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  embeddedInCard?: boolean;
  resyncVersion?: number;
  onError: (message: string | null) => void;
};

export function ProcessoDiagramComposedSection({
  processoId,
  getAccessToken,
  embeddedInCard = false,
  resyncVersion = 0,
  onError,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [at, setAt] = useState(todayDateInput());
  const [composed, setComposed] = useState<ComposedProcessoDiagram | null>(null);
  const [showDiff, setShowDiff] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const data = await fetchProcessoDiagramaComposed(processoId, getAccessToken, { at });
      setComposed(data);
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar diagrama composto.");
    } finally {
      setLoading(false);
    }
  }, [at, getAccessToken, onError, processoId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!resyncVersion) return;
    void load();
  }, [resyncVersion, load]);

  const conflictNodeIds = useMemo(() => {
    if (!composed?.conflicts?.length) return undefined;
    return {
      changed: [...new Set(composed.conflicts.map((c) => c.node_id))],
      added: [] as string[],
      removed: [] as string[],
    };
  }, [composed]);

  const displayFlowchart = useMemo(
    () => (composed?.flowchart ? stripFlowchartHighlights(composed.flowchart) : null),
    [composed]
  );

  if (loading && !composed) {
    return <p className="ds-hint">Carregando diagrama composto…</p>;
  }

  return (
    <div className="tm-diagram-composed">
      {!embeddedInCard ? (
        <FieldLabel
          className="tm-field__label"
          label="Diagrama composto"
          hint={TM_HELP_TOOLTIPS.processos.diagramaComposto}
        />
      ) : null}

      <div className="tm-decomposition-composed__toolbar">
        <label className="tm-decomposition-composed__date">
          <span className="ds-hint">Compor em</span>
          <NativeTextControl type="date" value={at} onChange={setAt} aria-label="Data de composição" />
        </label>
        <button type="button" className={DS_GHOST_BTN} disabled={loading} onClick={() => void load()}>
          {loading ? "Atualizando…" : "Atualizar"}
        </button>
      </div>

      {composed?.applied_revisoes?.length ? (
        <p className="ds-hint">
          {composed.applied_revisoes.length} revisão(ões) vigente(s) aplicadas
          {composed.conflicts?.length
            ? ` · ${composed.conflicts.length} conflito(s) de interseção`
            : ""}
          .
        </p>
      ) : (
        <p className="ds-hint">Nenhuma revisão vigente nesta data — exibindo o diagrama macro base.</p>
      )}

      {composed?.conflicts?.length ? (
        <DiffHighlightToggle
          active={showDiff}
          onChange={setShowDiff}
          summary={`${composed.conflicts.length} conflito(s) de interseção no mesmo nó.`}
        />
      ) : null}

      {showDiff && composed?.conflicts?.length ? (
        <div className="ds-state ds-state--warn" role="status">
          <p>
            Interseções no mesmo nó: o rótulo exibido é o da revisão com início de vigência mais
            recente.
          </p>
          <ul className="tm-decomposition-composed__conflicts">
            {composed.conflicts.map((conflict) => (
              <li key={`${conflict.node_id}-${conflict.field}`}>
                Nó <code>{conflict.node_id}</code> ({conflict.field}):{" "}
                {conflict.revisoes
                  .map((r) => r.versao_revisao || r.revisao_id.slice(0, 8))
                  .join(" × ")}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {displayFlowchart ? (
        <>
          <FlowchartEditor
            value={displayFlowchart}
            readOnly
            diffNodeIds={showDiff ? conflictNodeIds : undefined}
          />
          {composed?.mermaid ? (
            <details className="tm-diagram-section__preview" open={false}>
              <summary>Preview Mermaid (composto)</summary>
              <DiagramMermaidPreview code={composed.mermaid} />
            </details>
          ) : null}
        </>
      ) : (
        <p className="ds-hint">Diagrama macro vazio. Cadastre o fluxo no processo.</p>
      )}
    </div>
  );
}
