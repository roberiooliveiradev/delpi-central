type CustomerContactsStubProps = {
  onAdd?: () => void;
};

/**
 * Contatos principais — placeholder até existir API de contatos.
 */
export function CustomerContactsStub({ onAdd }: CustomerContactsStubProps) {
  return (
    <section className="pva-card pva-contacts-stub" aria-label="Contatos principais">
      <h2 className="pva-contacts-stub__title">Contatos principais</h2>
      <p className="pva-contacts-stub__empty">
        Ainda não há contatos cadastrados para este cliente. Em breve você poderá
        registrar compradores, financeiro e outros interlocutores aqui.
      </p>
      <button
        type="button"
        className="pva-btn pva-btn--secondary pva-contacts-stub__add"
        onClick={onAdd}
        disabled={!onAdd}
        title={onAdd ? undefined : "Cadastro de contatos em breve"}
      >
        + Adicionar contato
      </button>
    </section>
  );
}
