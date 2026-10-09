import { useEffect, useMemo, useState } from "react";

import { BpmnDocumentEditorPage, type Capabilities } from "@delpi/bpmn-editor";
import "@delpi/bpmn-editor/styles.css";

import type { AppProps } from "../../App";
import { TmProcessDocumentHost } from "../../data/TmProcessDocumentHost";
import { fetchProcesso } from "../../data/api/transformometroApi";
import { usePortalSessionAccess } from "../../state/portalChrome";
import {
  buildProcessoBpmnRevisionPath,
  buildProcessoPath,
} from "../../utils/routeParser";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  onNavigate: (path: string) => void;
};

/** Wrapper Transformômetro: injeta o host do documento BPMN nativo do
 *  processo na superfície de edição compartilhada (G7 / ADR-006). */
export function ProcessBpmnEditorPage({
  processoId,
  getAccessToken,
  onNavigate,
}: Props) {
  const { isSuperadmin, permissions } = usePortalSessionAccess();
  const [title, setTitle] = useState("Documento BPMN");

  useEffect(() => {
    let cancelled = false;
    void fetchProcesso(processoId, getAccessToken)
      .then((processo) => {
        if (cancelled) return;
        const label = [processo?.codigo_processo, processo?.nome_processo]
          .filter(Boolean)
          .join(" — ");
        if (label) setTitle(label);
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [processoId, getAccessToken]);

  const host = useMemo(
    () => new TmProcessDocumentHost(processoId, title, getAccessToken),
    [processoId, title, getAccessToken],
  );

  const capabilities: Capabilities = useMemo(() => {
    // G7: autorização do documento é por PROCESSO — backend exige apenas
    // `transformometro.access` (mesma policy do G5; manage granular é
    // melhoria registrada). canManage libera criar/restaurar revisões.
    const hasAccess =
      isSuperadmin || permissions.includes("transformometro.access");
    return { view: hasAccess, edit: hasAccess, manage: hasAccess };
  }, [isSuperadmin, permissions]);

  return (
    <BpmnDocumentEditorPage
      host={host}
      capabilities={capabilities}
      backLabel="Voltar ao processo"
      backPath={buildProcessoPath(processoId)}
      revisionPathFor={(n) => buildProcessoBpmnRevisionPath(processoId, n)}
      navigate={onNavigate}
    />
  );
}
