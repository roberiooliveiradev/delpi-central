import "./codigo.css";

const PDF_PATH = "/apps/codigo-etica/documents/codigo-de-etica.pdf";
const PDF_FILENAME = "codigo-de-etica.pdf";

export function CodigoEticaPublicView() {
  return (
    <div className="ce-pub">
      <header className="ce-pub__header">
        <p className="ce-pub__eyebrow">Institucional · Conduta</p>
        <h1>Código de Ética</h1>
        <p className="ce-pub__lead">
          Consulte o Código de Ética da DELPI sem precisar de conta no Minha DELPI.
          O documento orienta princípios, valores e condutas esperadas no ambiente de trabalho.
        </p>
        <div className="ce-pub__actions">
          <a className="ce-pub__btn" href={PDF_PATH} target="_blank" rel="noreferrer">
            Abrir em nova aba
          </a>
          <a className="ce-pub__btn ce-pub__btn--ghost" href={PDF_PATH} download={PDF_FILENAME}>
            Baixar PDF
          </a>
        </div>
      </header>
      <iframe
        className="ce-pub__frame"
        title="Código de Ética da DELPI"
        src={PDF_PATH}
      />
    </div>
  );
}
