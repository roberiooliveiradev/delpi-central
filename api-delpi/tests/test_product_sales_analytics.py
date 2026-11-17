from datetime import date
import pytest
from app.domain.services.product.product_sales_analytics import first_day_of_window, summarize_product_sales

def test_ray_product_aggregation_and_empty_months():
    assert first_day_of_window(12, date(2026,11,17)) == date(2025,12,1)
    result = summarize_product_sales([
      {"month":"202611","customer_code":"0001","customer_store":"01",
       "customer_name":"Cliente 1","gross_quantity":200,"returned_quantity":30},
      {"month":"202610","customer_code":"0002","customer_store":"01",
       "customer_name":"Cliente 2","gross_quantity":50,"returned_quantity":0},
    ], months=12, today=date(2026,11,17))
    assert len(result["monthly"]) == 12
    assert result["monthly"][0]["month"] == "2025-12"
    assert result["monthly"][0]["quantity"] == 0
    assert result["summary"]["gross_quantity"] == 250
    assert result["summary"]["returned_quantity"] == 30
    assert result["summary"]["total_quantity"] == 220
    assert result["summary"]["monthly_average"] == pytest.approx(220/12)
    assert result["summary"]["customer_count"] == 2

def test_negative_devolucoes_and_unsupported_periods():
    result = summarize_product_sales([
      {"month":"202601","customer_code":"C","customer_store":"01",
       "customer_name":"Cliente","gross_quantity":10,"returned_quantity":0},
      {"month":"202602","customer_code":"C","customer_store":"01",
       "customer_name":"Cliente","gross_quantity":0,"returned_quantity":20},
    ], months=24, today=date(2026,11,17))
    assert result["summary"]["total_quantity"] == -10
    assert result["customers"][0]["quantity"] == -10
    with pytest.raises(ValueError):
        first_day_of_window(13,date(2026,11,17))
