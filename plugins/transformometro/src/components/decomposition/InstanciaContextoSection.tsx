import { useCallback, useEffect, useState } from "react";

import type { AppProps } from "../../App";
import { FieldLabel } from "../HelpTooltip";
import { TM_HELP_TOOLTIPS } from "../../content/helpTooltips";
import {
  fetchInstanciaContexto,
  saveInstanciaContexto,
} from "../../data/api/transformometroDecompositionApi";
import { emptyInstanciaContexto, type InstanciaContextoV1 } from "../../types/decomposition";

type Props = Pick<AppProps, "getAccessToken"> & {
  instanciaId: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  onError: (message: string | null) => void;
};

export function InstanciaContextoSection({
  instanciaId,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  onError,
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
    } catch (err) {
      onError(err instanceof Error ? err.message : "Erro ao salvar contexto operacional.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <p className="ds-hint">Carregando contexto operacional…</p>;
  }

  return (
    <div className="tm-instancia-contexto">
      {!embeddedInCard ? (
        <FieldLabel label="Contexto operacional" hint={TM_HELP_TOOLTIPS.decomposition.contextoInstancia} />
      ) : null}

      <div className="tm-inst-form__row">
        <label className="ds-field">
          <span className="ds-field-label">Responsável local</span>
          <input
            value={contexto.responsavel_local ?? ""}
            disabled={readOnly}
            onChange={(event) =>
              setContexto({ ...contexto, responsavel_local: event.target.value || null })
            }
          />
        </label>
        <label className="ds-field">
          <span className="ds-field-label">Contato</span>
          <input
            value={contexto.contato ?? ""}
            disabled={readOnly}
            onChange={(event) => setContexto({ ...contexto, contato: event.target.value || null })}
          />
        </label>
      </div>

      <label className="ds-field tm-inst-form__field--full">
        <span className="ds-field-label">Observações de rollout</span>
        <textarea
          rows={3}
          value={contexto.observacoes_rollout ?? ""}
          disabled={readOnly}
          onChange={(event) =>
            setContexto({ ...contexto, observacoes_rollout: event.target.value || null })
          }
        />
      </label>

      {!readOnly ? (
        <button type="button" className="ds-primary-btn" disabled={saving} onClick={() => void handleSave()}>
          {saving ? "Salvando…" : "Salvar contexto"}
        </button>
      ) : null}
    </div>
  );
}
