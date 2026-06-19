from app.domain.services.chat_pdf_annotation_table_service import ChatPdfAnnotationTableService


def test_build_tables_clusters_rows_by_y_position():
    annotations = [
        {"page": 1, "content": "ITEM", "bbox": [10, 100, 40, 112]},
        {"page": 1, "content": "QTD", "bbox": [60, 100, 90, 112]},
        {"page": 1, "content": "10080591", "bbox": [10, 120, 70, 132]},
        {"page": 1, "content": "1", "bbox": [60, 120, 80, 132]},
        {"page": 1, "content": "10090481", "bbox": [10, 140, 70, 152]},
        {"page": 1, "content": "2", "bbox": [60, 140, 80, 152]},
    ]

    tables = ChatPdfAnnotationTableService.build_tables(annotations)

    assert tables
    assert tables[0]["source"] == "pdf_annotations"
    assert tables[0]["rowCount"] >= 2
    assert "10080591" in ChatPdfAnnotationTableService.table_text(tables)
