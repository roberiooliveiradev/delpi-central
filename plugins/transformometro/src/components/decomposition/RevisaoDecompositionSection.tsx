import { useCallback, useEffect, useMemo, useState } from "react";

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
  type DecompositionOverlayV1,
  type DecompositionTreeV1,
} from "../../types/decomposition";
import { buildDecompositionRichTree } from "../../utils/decompositionRichTree";
import { DecompositionFlatPreview } from "./DecompositionFlatPreview";
import { DecompositionRichTree } from "./DecompositionRichTree";
import { TabPanelTransition } from "../TabPanelTransition";

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
  const [tab, setTab] = useState<"arvore" | "planilha">("arvore");

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

  const richRoot = useMemo(
    () =>
      mergedTree
        ? buildDecompositionRichTree(mergedTree, {
            title: processoNome ? `Mapeamento — ${processoNome}` : "Mapeamento da revisão",
            overlay,
          })
        : null,
    [mergedTree, overlay, processoNome]
  );

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

  return (
    <div className="tm-decomposition-revisao">
      {!embeddedInCard ? (
        <FieldLabel label="Mapeamento da revisão" hint={TM_HELP_TOOLTIPS.decomposition.mapeamentoRevisao} />
      ) : null}

      <div className="tm-decomposition-section__tabs">
        <button
          type="button"
          className={tab === "arvore" ? "ds-tab-btn is-active" : "ds-tab-btn"}
          onClick={() => setTab("arvore")}
        >
          Árvore
        </button>
        <button
          type="button"
          className={tab === "planilha" ? "ds-tab-btn is-active" : "ds-tab-btn"}
          onClick={() => setTab("planilha")}
        >
          Planilha
        </button>
      </div>

      <TabPanelTransition tabKey={tab}>
        {tab === "arvore" && richRoot ? (
          <DecompositionRichTree
            root={richRoot}
            expandDepth={2}
            renderLabel={
              readOnly
                ? undefined
                : (node) =>
                    node.id === "decomposition-root" ? (
                      <span className="tm-rich-tree__label">{node.label}</span>
                    ) : (
                      <input
                        className="tm-rich-tree__input"
                        value={overlay.node_overrides?.[node.id]?.label ?? node.label}
                        onChange={(event) => updateOverride(node.id, event.target.value)}
                        aria-label={`Rótulo ${node.label}`}
                      />
                    )
            }
          />
        ) : null}

        {tab === "planilha" ? (
          <DecompositionFlatPreview tree={mergedTree} macroprocesso={processoNome} />
        ) : null}
      </TabPanelTransition>

      {!readOnly ? (
        <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
          {saving ? "Salvando…" : "Salvar mapeamento da revisão"}
        </button>
      ) : null}
    </div>
  );
}
