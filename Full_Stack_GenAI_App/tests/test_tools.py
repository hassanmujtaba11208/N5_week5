import pytest
from backend.app.tools.calculator import calculate
from backend.app.services.rag import RAGService
from backend.app.config import KNOWLEDGE_BASE_PATH


def test_calculator():
    assert calculate("125 * (8 + 2)") == 1250


def test_calculator_rejects_python_execution():
    with pytest.raises((ValueError, SyntaxError)):
        calculate("__import__('os').system('whoami')")


def test_rag_returns_relevant_passage():
    rag = RAGService(KNOWLEDGE_BASE_PATH)
    results = rag.search("identify unusual sensor readings and anomaly detection", 3)
    assert results
    assert results[0]["section"] == "Anomaly Detection"
