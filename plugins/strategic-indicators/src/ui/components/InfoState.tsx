type InfoStateProps = {
  title: string;
  description: string;
};

export function InfoState({ title, description }: InfoStateProps) {
  return (
    <div className="si-info-state">
      <div className="si-info-state__icon">i</div>
      <div className="si-info-state__content">
        <h3 className="si-info-state__title">{title}</h3>
        <p className="si-info-state__description">{description}</p>
      </div>
    </div>
  );
}