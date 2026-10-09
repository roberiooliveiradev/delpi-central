"""Re-export compat — fábrica de artefato em branco vive em
``shared/bpmn_validation`` (G7)."""

from bpmn_validation.blank import IdGeneratorLike, TemplateBlankArtifactFactory

__all__ = ["IdGeneratorLike", "TemplateBlankArtifactFactory"]
