import { ActionButton } from "@delpi/plugin-ui/index";

type ErrorStateProps = {
  message: string;
  onRetry?: () => void;
};

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="fi-state fi-state--error" role="alert">
      <p>{message}</p>
      {onRetry ? (
        <ActionButton variant="ghost" onClick={onRetry}>
          Tentar novamente
        </ActionButton>
      ) : null}
    </div>
  );
}
