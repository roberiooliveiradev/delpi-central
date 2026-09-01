import { ModalShell, modalShellBemClasses } from "@delpi/plugin-ui/index";

import { PpActionButton } from "../../app/productionPulseUi";
import { PP_HELP } from "../../content/helpTooltips";
import type { ProbeResult } from "../../types/form";
import { formatPrimaryMetricFromProbe } from "../../utils/deviceFormValidation";

type TestConnectionModalProps = {
  open: boolean;
  loading: boolean;
  result: ProbeResult | null;
  error: string | null;
  onClose: () => void;
};

export function TestConnectionModal({
  open,
  loading,
  result,
  error,
  onClose,
}: TestConnectionModalProps) {
  const success = result?.online === true;
  const metricSummary = result ? formatPrimaryMetricFromProbe(result.metrics) : null;

  return (
    <ModalShell
      open={open}
      title="Testar conexão"
      onClose={onClose}
      classNames={modalShellBemClasses("pp")}
    >
      <div className="pp-test-modal">
        {loading ? <p>Testando comunicação com o device…</p> : null}
        {!loading && success ? (
          <>
            <p>{PP_HELP.modals.testOk}</p>
            {metricSummary ? <p className="pp-test-modal__metric">{metricSummary}</p> : null}
            {result?.latencyMs != null ? (
              <p className="pp-test-modal__meta">Latência: {result.latencyMs} ms</p>
            ) : null}
          </>
        ) : null}
        {!loading && !success ? (
          <p className="pp-test-modal__error">{error ?? PP_HELP.modals.testFail}</p>
        ) : null}
        <div className="pp-test-modal__actions">
          <PpActionButton variant="primary" onClick={onClose}>
            Fechar
          </PpActionButton>
        </div>
      </div>
    </ModalShell>
  );
}
