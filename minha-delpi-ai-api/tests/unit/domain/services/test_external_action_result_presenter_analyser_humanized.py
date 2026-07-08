"""Fixture canônica de payload /analyser para testes de desenho e validação."""


def _analyser_payload_with_guide_and_inspection():
    return {
        "product": {
            "code": "90260140",
            "description": "CHICOTE  EPR SINGELO 1400MM",
            "type": "PA",
            "unit": "MI",
            "group_code": "9026",
            "active": "S",
            "blocked": "2",
            "customer_reference": "10156005",
            "default_warehouse": "01",
            "last_purchase_price": 0.0,
            "standard_cost": 6079.8802,
            "last_revision_date": "20250702",
            "ncm_ipi_position": "85444200",
            "drawing_code": "0118.6302",
        },
        "guide": {
            "items": [
                {
                    "product_code": "90260140",
                    "bom_level": 0,
                    "operations": [
                        {
                            "operation_code": "01",
                            "operation_description": "CORTAR TUBO MAIOR E MENOR",
                            "work_center": "CT-19",
                        },
                        {
                            "operation_code": "05",
                            "operation_description": "INSPECIONAR",
                            "work_center": "CT-70",
                        },
                    ],
                },
                {
                    "product_code": "50212194",
                    "bom_level": 1,
                    "operations": [
                        {
                            "operation_code": "01",
                            "operation_description": "CORTAR E DECAPAR",
                            "work_center": "CT-33",
                        }
                    ],
                },
            ],
            "total": 2,
        },
        "inspection": {
            "items": [
                {
                    "product": "90260140",
                    "level": 0,
                    "QP6": [
                        {
                            "QP6_PRODUT": "90260140",
                            "QP6_DESCPO": "CHICOTE  EPR SINGELO 1400MM",
                        }
                    ],
                    "QP7": [
                        {
                            "QP7_OPERAC": "01",
                            "QP7_ENSAIO": "506",
                            "QP7_LABOR": "LABFIS",
                            "QP7_NOMINA": "500",
                            "QP7_LIE": "495",
                            "QP7_LSE": "505",
                            "QP7_UNIMED": "MM",
                        }
                    ],
                    "QP8": [
                        {
                            "QP8_OPERAC": "01",
                            "QP8_ENSAIO": "504",
                            "QP8_TEXTO": "10120005",
                        }
                    ],
                },
                {
                    "product": "10120001",
                    "parentCode": "90260140",
                    "level": 1,
                },
            ],
            "total": 2,
        },
        "structure": {
            "root": {"code": "90260140", "description": "CHICOTE", "type": "PA"},
            "items": [
                {
                    "code": "50212194",
                    "description": "CB20PRET",
                    "type": "PI",
                    "unit": "MI",
                    "quantity": 2.0,
                    "components": [],
                }
            ],
            "total": 1,
        },
    }
