import { ModalShell, modalShellBemClasses } from "@delpi/plugin-ui/index";

import { PpActionButton } from "../../app/productionPulseUi";

type CommandJsonModalProps = {
  open: boolean;
  title: string;
  payload: Record<string, unknown>;
  onClose: () => void;
};

export function CommandJsonModal({ open, title, payload, onClose }: CommandJsonModalProps) {
  return (
    <ModalShell open={open} title={title} onClose={onClose} classNames={modalShellBemClasses("pp")}>
      <div className="pp-modal-body">
        <pre className="pp-json-preview">{JSON.stringify(payload, null, 2)}</pre>
        <div className="pp-modal-body__actions">
          <PpActionButton variant="primary" onClick={onClose}>
            Fechar
          </PpActionButton>
        </div>
      </div>
    </ModalShell>
  );
}
