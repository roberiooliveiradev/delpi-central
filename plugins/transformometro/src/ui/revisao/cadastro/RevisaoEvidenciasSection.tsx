import type { AppProps } from "../../../App";
import { RevisaoEvidencePanel } from "../../../components/evidence/RevisaoEvidencePanel";

type Props = Pick<AppProps, "getAccessToken"> & {
  revisaoId: string;
  onError: (message: string | null) => void;
  onReload?: () => void;
};

export function RevisaoEvidenciasSection({
  revisaoId,
  getAccessToken,
  onError,
  onReload,
}: Props) {
  return (
    <RevisaoEvidencePanel
      revisaoId={revisaoId}
      getAccessToken={getAccessToken}
      onError={onError}
      onChanged={onReload}
    />
  );
}
