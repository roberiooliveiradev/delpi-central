import { useMemo, useRef } from "react";

import { BpmnRevisionViewPage } from "@delpi/bpmn-editor";
import "@delpi/bpmn-editor/styles.css";

import type { AppProps } from "../../App";
import { TmProcessDocumentHost } from "../../data/TmProcessDocumentHost";
import {
  buildProcessoBpmnEditPath,
} from "../../utils/routeParser";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  revisionNumber: number;
  onNavigate: (path: string) => void;
};

/** Wrapper Transformômetro: view de revisão histórica do documento BPMN
 *  nativo do processo (read-only, artefato imutável). */
export function ProcessBpmnRevisionViewPage({
  processoId,
  revisionNumber,
  getAccessToken,
  onNavigate,
}: Props) {
  // Host estável por processo (G9-LOAD-1 §3): token via getter vivo —
  // identidade de callback nunca recria o host.
  const tokenRef = useRef(getAccessToken);
  tokenRef.current = getAccessToken;
  const host = useMemo(
    () =>
      new TmProcessDocumentHost(
        processoId,
        "Documento BPMN",
        () => tokenRef.current?.(),
      ),
    [processoId],
  );

  return (
    <BpmnRevisionViewPage
      host={host}
      revisionNumber={revisionNumber}
      backLabel="Voltar ao diagrama"
      backPath={buildProcessoBpmnEditPath(processoId)}
      navigate={onNavigate}
    />
  );
}
