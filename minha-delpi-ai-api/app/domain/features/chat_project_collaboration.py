"""Projetos colaborativos — compartilhamento entre usuários e contexto entre conversas.

Desabilitado até implementação futura (jun/2026). Ver:
``docs/roadmap/projetos-colaborativos-futuro.md``.
"""

from __future__ import annotations

# Quando True: rotas /share, /shares e shareConversationContext ficam ativos.
PROJECT_COLLABORATION_ENABLED = False


def is_project_collaboration_enabled() -> bool:
    return PROJECT_COLLABORATION_ENABLED
