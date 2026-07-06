import { useCallback, useEffect, useState } from "react";

import type { AppProps } from "../../App";
import { FieldLabel } from "../HelpTooltip";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  fetchInstanciaContexto,
  saveInstanciaContexto,
} from "../../data/api/transformometroDecompositionApi";
import { emptyInstanciaContexto, type InstanciaContextoV1 } from "../../types/decomposition";
import { InstanciaContextoReadView } from "./InstanciaContextoReadView";

const C = TM_HELP_TOOLTIPS.decomposition;

type Props = Pick<AppProps, "getAccessToken"> & {
  instanciaId: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  onError: (message: string | null) => void;
  onSaved?: () => void;
};

export function InstanciaContextoSection({
  instanciaId,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  onError,
  onSaved,
}: Props) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [contexto, setContexto] = useState<InstanciaContextoV1>(emptyInstanciaContexto());

  const load = useCallback(async () => {
    setLoading(true);
    onError(null);
    try {
      const data = await fetchInstanciaContexto(instanciaId, getAccessToken);
      setContexto(data.conteudo ?? emptyInstanciaContexto());
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao carregar contexto operacional.");
    } finally {
      setLoading(false);
    }
  }, [getAccessToken, instanciaId, onError]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSave() {
    setSaving(true);
    onError(null);
    try {
      await saveInstanciaContexto(instanciaId, contexto, getAccessToken);
      await load();
      onSaved?.();
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar contexto operacional.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="ds-hint">Carregando contexto operacional…</p>;
  }

  if (readOnly) {
    return (
      <div className="tm-instancia-contexto">
        <InstanciaContextoReadView contexto={contexto} />
      </div>
    );
  }

  return (
    <div className="tm-instancia-contexto">
      {!embeddedInCard ? (
        <FieldLabel label="Contexto operacional" hint={C.contextoInstancia} />
      ) : null}

      <div className="tm-inst-form__row">
        <label className="ds-field">
          <FieldLabel label="Responsável local" hint={C.contextoResponsavel} />
          <input
            value={contexto.responsavel_local ?? ""}
            onChange={(event) =>
              setContexto({ ...contexto, responsavel_local: event.target.value || null })
            }
          />
        </label>
        <label className="ds-field">
          <FieldLabel label="Contato" hint={C.contextoContato} />
          <input
            value={contexto.contato ?? ""}
            onChange={(event) => setContexto({ ...contexto, contato: event.target.value || null })}
          />
        </label>
      </div>

      <label className="ds-field tm-inst-form__field--full">
        <FieldLabel label="Observações de rollout" hint={C.contextoObservacoesRollout} />
        <textarea
          rows={3}
          value={contexto.observacoes_rollout ?? ""}
          onChange={(event) =>
            setContexto({ ...contexto, observacoes_rollout: event.target.value || null })
          }
        />
      </label>

      <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
        {saving ? "Salvando…" : "Salvar contexto"}
      </button>
    </div>
  );
}
