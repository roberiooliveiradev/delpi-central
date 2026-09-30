import type { ElementSummary } from "../BpmnEditorAdapter";

type Props = {
  element: ElementSummary | null;
};

/**
 * Inspector product-owned (P4 §30): exibido em read-only no lugar do
 * bpmn-js-properties-panel (que só existe no modo editable).
 */
export function ElementInspector({ element }: Props) {
  if (!element) {
    return <p className="bpmnm-hint">Selecione um elemento no diagrama.</p>;
  }
  const attrs = Object.entries(element.attributes);
  return (
    <dl className="bpmnm-inspector">
      <dt>ID</dt>
      <dd><code>{element.id}</code></dd>
      <dt>Tipo</dt>
      <dd><code>{element.type}</code></dd>
      {element.name ? (
        <>
          <dt>Nome</dt>
          <dd>{element.name}</dd>
        </>
      ) : null}
      {element.documentation ? (
        <>
          <dt>Documentação</dt>
          <dd>{element.documentation}</dd>
        </>
      ) : null}
      {attrs.length > 0 ? (
        <>
          <dt>Atributos</dt>
          <dd>
            <ul>
              {attrs.map(([key, value]) => (
                <li key={key}>
                  <code>{key}</code> = {value}
                </li>
              ))}
            </ul>
          </dd>
        </>
      ) : null}
    </dl>
  );
}
