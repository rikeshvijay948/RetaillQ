"""
Unit tests for the Evidence-Grounded AI Copilot and Deterministic Fallback Engine.
"""
import copilot


def test_extract_potential_product_name():
    """Verify regex and token extraction for catalog and non-catalog products."""
    # Known catalog tokens
    assert copilot.extract_potential_product_name("Tell me about espresso") == "Organic Fair-Trade Espresso Beans (1kg)"
    assert copilot.extract_potential_product_name("What is the status of headphones?") == "Ultra ANC Wireless Headphones"

    # SKU extraction
    assert copilot.extract_potential_product_name("Check SKU-ELC-001") == "Ultra ANC Wireless Headphones"

    # Out-of-catalog items
    assert copilot.extract_potential_product_name("Do we sell iPhones?") == "iPhones"


def test_intent_classification():
    """Verify that user queries route to the exact designated deterministic intent."""
    test_cases = [
        ("Which products need attention today?", "CRITICAL_INVENTORY_ATTENTION"),
        ("What are our top 5 products by revenue?", "TOP_PRODUCTS_RANKING"),
        ("Which product has the highest revenue?", "HIGHEST_REVENUE_PRODUCT"),
        ("If I can only reorder two products today, which should I prioritize?", "RESTOCK_PRIORITIZATION"),
        ("Who are our suppliers?", "SUPPLIER_PERFORMANCE"),
        ("Do we sell iPhones?", "PRODUCT_CATALOG_LOOKUP"),
        ("What is our category performance?", "CATEGORY_PERFORMANCE"),
        ("Show me daily sales trends", "SALES_TRENDS"),
        ("Give me an executive overview of the business", "EXECUTIVE_OVERVIEW"),
    ]

    for query, expected_intent in test_cases:
        intent, func_name, context = copilot.classify_intent(query)
        assert intent == expected_intent, f"Failed for query: '{query}' -> got '{intent}', expected '{expected_intent}'"
        assert len(func_name) > 0
        assert isinstance(context, dict)


def test_iphone_zero_hallucination():
    """Verify out-of-catalog search returns explicit non-existence instead of hallucination."""
    res = copilot.generate_copilot_response("Do we sell iPhones?")
    assert "No iPhone product was found in the current RetailIQ dataset" in res["answer"]
    assert res["intent"] == "PRODUCT_CATALOG_LOOKUP"
    assert len(res["evidence_metrics"]) == 0


def test_reorder_two_priority():
    """Verify prioritization selects exactly two items with the lowest runway remaining."""
    res = copilot.generate_copilot_response("If I can only reorder two products today, which should I prioritize?")
    assert res["intent"] == "RESTOCK_PRIORITIZATION"
    assert len(res["evidence_metrics"]) == 2
    # Ensure Espresso Beans (0.53d) and Headphones (0.59d) are prioritized
    answer_text = res["answer"]
    assert "Organic Fair-Trade Espresso Beans" in answer_text
    assert "Ultra ANC Wireless Headphones" in answer_text


def test_highest_revenue_answer():
    """Verify highest revenue query returns #1 earner (Ultra ANC Headphones)."""
    res = copilot.generate_copilot_response("Which product has the highest revenue?")
    assert res["intent"] == "HIGHEST_REVENUE_PRODUCT"
    assert "Ultra ANC Wireless Headphones" in res["answer"]
    assert "22,798.48" in res["answer"]


def test_copilot_response_schema():
    """Verify response contains all required fields for frontend and proof drawer."""
    res = copilot.generate_copilot_response("Give me an executive overview")
    required_keys = [
        "answer",
        "evidence",
        "evidence_metrics",
        "recommendation",
        "recommendations",
        "confidence",
        "mode",
        "mode_label",
        "intent",
        "analytics_function",
        "suggested_followups",
        "provenance_chain"
    ]
    for key in required_keys:
        assert key in res, f"Missing required response key: {key}"
