import tempfile
from pathlib import Path

from app.application.services.chat_attachment_text_extractor import ChatAttachmentTextExtractor


def test_extract_csv_semicolon_delimiter():
    extractor = ChatAttachmentTextExtractor()

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "dados.csv"
        path.write_text(
            "Produto;Descricao;Qtd\n10080001;Parafuso;10\n",
            encoding="utf-8",
        )

        result = extractor.extract(
            storage_path=str(path),
            filename="dados.csv",
            content_type="text/csv",
        )

    assert result["supported"] is True
    first_line = result["content"].splitlines()[0]
    assert "Produto" in first_line and "Descricao" in first_line
