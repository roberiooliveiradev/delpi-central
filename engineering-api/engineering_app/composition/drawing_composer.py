"""Drawing analysis composition root (R6-B).

Registers the production default extraction provider. Adapters live in
infrastructure; this module is the ONLY allowed point that wires them.
"""

from __future__ import annotations

from engineering_app.application.drawing.extraction_ports import (
    set_default_extractor_factory,
)
from engineering_app.infrastructure.extraction.pypdf_adapter import (
    PypdfExtractionAdapter,
)

set_default_extractor_factory(PypdfExtractionAdapter)
