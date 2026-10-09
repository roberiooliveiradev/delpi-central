import { useMemo } from "react";

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
  const host = useMemo(
    () => new TmProcessDocumentHost(processoId, "Documento BPMN", getAccessToken),
    [processoId, getAccessToken],
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
