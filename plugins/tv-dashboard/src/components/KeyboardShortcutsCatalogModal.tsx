import { listKeyboardShortcutsByGroup, formatShortcutKeys } from "../content/keyboardShortcuts";
import { useKeyboardShortcutsTips } from "../context/KeyboardShortcutsTipsProvider";
import { Modal } from "./ui/Modal";

/** Modal com o catálogo completo de atalhos do editor. */
export function KeyboardShortcutsCatalogModal() {
  const { catalogOpen, closeCatalog } = useKeyboardShortcutsTips();
  const groups = listKeyboardShortcutsByGroup();

  return (
    <Modal
      open={catalogOpen}
      title="Atalhos do teclado"
      onClose={closeCatalog}
      className="td-modal--shortcuts"
    >
      <p className="td-shortcuts-catalog__lead">
        Pressione <kbd className="td-shortcuts-catalog__kbd">F</kbd> para KeyTips das abas e da
        ribbon (letra da aba, depois letra da ação; Esc volta). Toque{" "}
        <kbd className="td-shortcuts-catalog__kbd">Alt</kbd> para ligar/desligar balões dos atalhos
        Ctrl. No Mac, Ctrl vira ⌘.
      </p>
      <div className="td-shortcuts-catalog">
        {groups.map((group) => (
          <section key={group.group} className="td-shortcuts-catalog__group" aria-labelledby={`td-sc-${group.group}`}>
            <h3 id={`td-sc-${group.group}`} className="td-shortcuts-catalog__group-title">
              {group.label}
            </h3>
            <ul className="td-shortcuts-catalog__list">
              {group.entries.map((entry) => (
                <li key={entry.id} className="td-shortcuts-catalog__row">
                  <div className="td-shortcuts-catalog__copy">
                    <span className="td-shortcuts-catalog__label">{entry.label}</span>
                    {entry.description ? (
                      <span className="td-shortcuts-catalog__desc">{entry.description}</span>
                    ) : null}
                  </div>
                  <kbd className="td-shortcuts-catalog__kbd">{formatShortcutKeys(entry.keys)}</kbd>
                </li>
              ))}
            </ul>
          </section>
        ))}
      </div>
    </Modal>
  );
}
