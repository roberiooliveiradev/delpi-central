import type { DeviceCommandAudit } from "../../types/detail";
import { PpActionButton } from "../../app/productionPulseUi";
import { commandLabel, formatDateTime, formatIssuedByUser } from "../../utils/detailDisplay";

type CommandAuditCardProps = {
  command: DeviceCommandAudit;
  onViewJson: (command: DeviceCommandAudit) => void;
};

export function CommandAuditCard({ command, onViewJson }: CommandAuditCardProps) {
  return (
    <article className="pp-command-card">
      <header className="pp-command-card__header">
        <span>{formatDateTime(command.createdAt)}</span>
        <span className={command.success ? "pp-command-card__ok" : "pp-command-card__fail"}>
          {command.success ? "OK" : "Falha"}
        </span>
      </header>
      <div className="pp-command-card__body">
        <div>
          <span className="pp-command-card__label">Comando</span>
          <strong>{commandLabel(command.commandKey)}</strong>
        </div>
        <div>
          <span className="pp-command-card__label">Usuário</span>
          <strong>{formatIssuedByUser(command)}</strong>
        </div>
        {!command.success && command.errorMessage ? (
          <p className="pp-command-card__error">{command.errorMessage}</p>
        ) : null}
      </div>
      <PpActionButton variant="ghost" onClick={() => onViewJson(command)}>
        Ver JSON
      </PpActionButton>
    </article>
  );
}
