def test_health_is_public(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ask_rag_mode(client, auth_headers):
    response = client.post("/ask", headers=auth_headers, json={
        "query": "What does the knowledge base say about anomaly detection?",
        "mode": "rag",
        "top_k": 3,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "rag"
    assert data["tool_used"] == "rag"
    assert "Anomaly Detection" in data["answer"]


def test_ask_agent_calculator_mode(client, auth_headers):
    response = client.post("/ask", headers=auth_headers, json={
        "query": "What is 125 * (8 + 2)?",
        "mode": "agent",
        "top_k": 3,
    })
    assert response.status_code == 200
    assert "1250" in response.json()["answer"]
    assert response.json()["tool_used"] == "calculator"


def test_ask_agent_datetime_mode(client, auth_headers):
    response = client.post("/ask", headers=auth_headers, json={
        "query": "What is today's date and current time?",
        "mode": "agent",
        "top_k": 3,
    })
    assert response.status_code == 200
    assert "Current local date" in response.json()["answer"]
    assert response.json()["tool_used"] == "datetime"


def test_ask_agent_ambiguous_query(client, auth_headers):
    response = client.post("/ask", headers=auth_headers, json={
        "query": "Can you help me with this?",
        "mode": "agent",
        "top_k": 3,
    })
    assert response.status_code == 200
    assert "clarify" in response.json()["answer"].lower()
