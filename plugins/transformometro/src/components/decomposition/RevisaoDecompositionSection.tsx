import { useCallback, useEffect, useState } from "react";

import type { AppProps } from "../../App";
import { FieldLabel } from "../HelpTooltip";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  fetchRevisaoDecomposicaoMerged,
  fetchRevisaoDecomposicaoOverlay,
  saveRevisaoDecomposicaoOverlay,
} from "../../data/api/transformometroDecompositionApi";
import {
  emptyDecompositionOverlay,
  sortDecompositionNodes,
  type DecompositionOverlayV1,
  type DecompositionTreeV1,
} from "../../types/decomposition";
import { DecompositionFlatPreview } from "./DecompositionFlatPreview";

type Props = Pick<AppProps, "getAccessToken"> & {
  revisaoId: string;
  processoNome?: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  resyncVersion?: number;
  onError: (message: string | null) => void;
};

export function RevisaoDecompositionSection({
  revisaoId,
  processoNome,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  resyncVersion = 0,
  onError,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [mergedTree, setMergedTree] = useState<DecompositionTreeV1 | null>(null);
  const [overlay, setOverlay] = useState<DecompositionOverlayV1>(emptyDecompositionOverlay());

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const [merged, overlayData] = await Promise.all([
        fetchRevisaoDecomposicaoMerged(revisaoId, getAccessToken),
        fetchRevisaoDecomposicaoOverlay(revisaoId, getAccessToken),
      ]);
      setMergedTree(merged.tree);
      setOverlay(overlayData.conteudo ?? emptyDecompositionOverlay());
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar mapeamento da revisão.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, onError, revisaoId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!resyncVersion) return;
    void load();
  }, [resyncVersion, load]);

  function updateOverride(nodeId: string, label: string) {
    setOverlay((current) => ({
      ...current,
      node_overrides: {
        ...(current.node_overrides ?? {}),
        [nodeId]: {
          ...(current.node_overrides?.[nodeId] ?? {}),
          label,
          highlight: "tobe",
        },
      },
    }));
  }

  async function handleSave() {
    setSaving(true);
    onError(null);
    try {
      await saveRevisaoDecomposicaoOverlay(revisaoId, overlay, getAccessToken);
      await load();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar overlay de mapeamento.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="ds-hint">Carregando mapeamento da revisão…</p>;
  }

  if (!mergedTree || !mergedTree.nodes.length) {
    return (
      <p className="ds-hint">
        Nenhum mapeamento no escopo desta instância. Cadastre a árvore no processo-mestre e o escopo na instância.
      </p>
    );
  }

  const nodes = sortDecompositionNodes(mergedTree.nodes);

  return (
    <div className="tm-decomposition-revisao">
      {!embeddedInCard ? (
        <FieldLabel label="Mapeamento da revisão" hint={TM_HELP_TOOLTIPS.decomposition.mapeamentoRevisao} />
      ) : null}

      <ul className="tm-decomposition-tree">
        {nodes.map((node) => {
          const overrideLabel = overlay.node_overrides?.[node.id]?.label;
          return (
            <li key={node.id} className="tm-decomposition-tree__item">
              <span className="tm-decomposition-tree__badge">{node.level}</span>
              {readOnly ? (
                <span>{overrideLabel ?? node.label}</span>
              ) : (
                <input
                  className="tm-decomposition-tree__input"
                  value={overrideLabel ?? node.label}
                  onChange={(event) => updateOverride(node.id, event.target.value)}
                />
              )}
            </li>
          );
        })}
      </ul>

      <DecompositionFlatPreview tree={mergedTree} macroprocesso={processoNome} />

      {!readOnly ? (
        <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
          {saving ? "Salvando…" : "Salvar mapeamento da revisão"}
        </button>
      ) : null}
    </div>
  );
}
