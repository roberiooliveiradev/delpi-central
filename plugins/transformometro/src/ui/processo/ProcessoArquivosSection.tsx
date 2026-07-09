import type { AppProps } from "../../App";
import { ProcessoArquivoPanel } from "../../components/evidence/ProcessoArquivoPanel";

type Props = Pick<AppProps, "getAccessToken"> & {
  processoId: string;
  readOnly?: boolean;
  embeddedInCard?: boolean;
  resyncVersion?: number;
  onError: (message: string | null) => void;
  onChanged?: () => void;
};

export function ProcessoArquivosSection({
  processoId,
  getAccessToken,
  readOnly = false,
  embeddedInCard = false,
  resyncVersion = 0,
  onError,
  onChanged,
}: Props) {
  return (
    <ProcessoArquivoPanel
      processoId={processoId}
      getAccessToken={getAccessToken}
      readOnly={readOnly}
      hideHeader={embeddedInCard}
      resyncVersion={resyncVersion}
      onError={onError}
      onChanged={onChanged}
    />
  );
}
