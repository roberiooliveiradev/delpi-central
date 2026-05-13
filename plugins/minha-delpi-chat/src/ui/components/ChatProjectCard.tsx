import {
  Folder,
  MoreHorizontal,
  Pencil,
  Trash2,
} from "lucide-react";
import { useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import type { ChatProject } from "../../data/api/chatTypes";

import "./ChatProjectCard.css";

type ChatProjectCardProps = {
  project: ChatProject;
  active?: boolean;
  onSelect: () => void;
  onOpenSettings?: () => void;
  onDelete?: () => void;
};

type MenuPosition = {
  top: number;
  left: number;
};

const MENU_WIDTH = 210;
const MENU_MARGIN = 8;

export function ChatProjectCard({
  project,
  active,
  onSelect,
  onOpenSettings,
  onDelete,
}: ChatProjectCardProps) {
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [position, setPosition] = useState<MenuPosition>({ top: 0, left: 0 });

  function updatePosition() {
    const trigger = triggerRef.current;

    if (!trigger) {
      return;
    }

    const rect = trigger.getBoundingClientRect();
    const preferredLeft = rect.right + MENU_MARGIN;
    const fallbackLeft = rect.left - MENU_WIDTH - MENU_MARGIN;

    const left =
      preferredLeft + MENU_WIDTH <= window.innerWidth - MENU_MARGIN
        ? preferredLeft
        : Math.max(MENU_MARGIN, fallbackLeft);

    setPosition({
      top: Math.max(MENU_MARGIN, rect.top),
      left,
    });
  }

  useLayoutEffect(() => {
    if (!isMenuOpen) {
      return;
    }

    updatePosition();

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setIsMenuOpen(false);
      }
    }

    window.addEventListener("resize", updatePosition);
    window.addEventListener("scroll", updatePosition, true);
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      window.removeEventListener("resize", updatePosition);
      window.removeEventListener("scroll", updatePosition, true);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [isMenuOpen]);

  const menu = isMenuOpen ? (
    <>
      <div
        className="mdc-chat-project-card-menu__scrim"
        role="presentation"
        onMouseDown={() => setIsMenuOpen(false)}
      />

      <div
        className="mdc-chat-project-card-menu__panel"
        role="menu"
        style={{ top: position.top, left: position.left }}
        onMouseDown={(event) => event.stopPropagation()}
      >
        <button
          type="button"
          role="menuitem"
          onClick={(event) => {
            event.stopPropagation();
            setIsMenuOpen(false);
            onOpenSettings?.();
          }}
        >
          <Pencil size={17} aria-hidden="true" />
          <span>Renomear</span>
        </button>

        <button
          type="button"
          role="menuitem"
          className="mdc-chat-project-card-menu__danger"
          onClick={(event) => {
            event.stopPropagation();
            setIsMenuOpen(false);
            onDelete?.();
          }}
        >
          <Trash2 size={17} aria-hidden="true" />
          <span>Excluir projeto</span>
        </button>
      </div>
    </>
  ) : null;

  return (
    <div
      className={
        active
          ? "mdc-chat-project-card mdc-chat-project-card--active"
          : "mdc-chat-project-card"
      }
    >
      <button
        type="button"
        className="mdc-chat-project-card__main"
        onClick={onSelect}
        title={project.description || project.name}
      >
        <span className="mdc-chat-project-card__icon">
          <Folder size={15} aria-hidden="true" />
        </span>

        <span className="mdc-chat-project-card__content">
          <strong>{project.name}</strong>
        </span>
      </button>

      <button
        ref={triggerRef}
        type="button"
        className="mdc-chat-project-card__options"
        aria-label="Opções do projeto"
        aria-expanded={isMenuOpen}
        title="Opções"
        onClick={(event) => {
          event.stopPropagation();
          updatePosition();
          setIsMenuOpen((current) => !current);
        }}
      >
        <MoreHorizontal size={16} aria-hidden="true" />
      </button>

      {menu ? createPortal(menu, document.body) : null}
    </div>
  );
}
