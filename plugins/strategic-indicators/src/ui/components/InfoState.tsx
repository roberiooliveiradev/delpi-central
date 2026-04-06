type InfoStateProps = {
  title: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
};

export function InfoState({
  title,
  description,
  actionLabel,
  onAction,
}: InfoStateProps) {
  const shouldRenderAction = Boolean(actionLabel && onAction);

  return (
    <div className="si-info-state">
      <div className="si-info-state__icon">i</div>
      <div className="si-info-state__content">
        <h3 className="si-info-state__title">{title}</h3>
        <p className="si-info-state__description">{description}</p>

        {shouldRenderAction ? (
          <button
            type="button"
            className="si-info-state__action"
            onClick={onAction}
          >
            {actionLabel}
          </button>
        ) : null}
      </div>
    </div>
  );
}