import { useEffect, useMemo, useRef, useState } from "react";

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
  const tokenRef = useRef(getAccessToken);
  tokenRef.current = getAccessToken;

  useEffect(() => {
    let cancelled = false;
    void fetchProcesso(processoId, () => tokenRef.current?.())
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
  }, [processoId]);

  // Host estável por processo (G9-LOAD-1 §3): title/token entram como
  // getters vivos — o host lê o valor mais recente no momento de cada
  // chamada e NUNCA é recriado por mudança de identidade de callback ou
  // pela chegada assíncrona do título (que causava um segundo loadModel
  // e a duplicação de requests document+working-copy).
  const titleRef = useRef(title);
  titleRef.current = title;
  const host = useMemo(
    () =>
      new TmProcessDocumentHost(
        processoId,
        () => titleRef.current,
        () => tokenRef.current?.(),
      ),
    [processoId],
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
