"""
Example tests for Living UI backend.

This file demonstrates the testing patterns the agent should follow.
The agent should create additional test files for custom models and routes.

DELETE this file after creating your own tests — it tests the template's
example endpoints which may be replaced by the agent.
"""


def test_health_check(client):
    """Health endpoint should always return 200."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_state_empty(client):
    """State should be empty dict initially."""
    response = client.get("/api/state")
    assert response.status_code == 200


def test_update_state(client):
    """Should be able to update state."""
    response = client.put("/api/state", json={"data": {"key": "value"}})
    assert response.status_code == 200

    # Verify state was updated
    response = client.get("/api/state")
    assert response.status_code == 200
    data = response.json()
    assert data.get("key") == "value"


def test_execute_action_reset(client):
    """Reset action should clear state."""
    # Set some state first
    client.put("/api/state", json={"data": {"counter": 5}})

    # Reset
    response = client.post("/api/action", json={"action": "reset"})
    assert response.status_code == 200
    assert response.json()["status"] == "reset"


# ============================================================================
# Example CRUD tests — agent should write similar tests for custom models
# ============================================================================
#
# def test_create_item(client):
#     """Should create a new item."""
#     response = client.post("/api/items", json={
#         "title": "Test Item",
#         "description": "A test item",
#     })
#     assert response.status_code == 200
#     data = response.json()
#     assert data["title"] == "Test Item"
#     assert "id" in data
#
#
# def test_create_and_get_item(client):
#     """Should be able to retrieve a created item."""
#     # Create
#     create_resp = client.post("/api/items", json={"title": "My Item"})
#     item_id = create_resp.json()["id"]
#
#     # Get
#     get_resp = client.get(f"/api/items/{item_id}")
#     assert get_resp.status_code == 200
#     assert get_resp.json()["title"] == "My Item"
#
#
# def test_update_item(client):
#     """Should update an existing item."""
#     # Create
#     create_resp = client.post("/api/items", json={"title": "Original"})
#     item_id = create_resp.json()["id"]
#
#     # Update
#     update_resp = client.put(f"/api/items/{item_id}", json={"title": "Updated"})
#     assert update_resp.status_code == 200
#     assert update_resp.json()["title"] == "Updated"
#
#
# def test_delete_item(client):
#     """Should delete an item."""
#     # Create
#     create_resp = client.post("/api/items", json={"title": "To Delete"})
#     item_id = create_resp.json()["id"]
#
#     # Delete
#     delete_resp = client.delete(f"/api/items/{item_id}")
#     assert delete_resp.status_code == 200
#
#     # Verify deleted
#     get_resp = client.get(f"/api/items/{item_id}")
#     assert get_resp.status_code == 404
#
#
# def test_delete_section_cascades(client):
#     """Deleting a section should delete all its cards."""
#     # Create section
#     section = client.post("/api/sections", json={"title": "My Section"}).json()
#
#     # Add cards
#     client.post("/api/cards", json={"title": "Card 1", "section_id": section["id"]})
#     client.post("/api/cards", json={"title": "Card 2", "section_id": section["id"]})
#
#     # Delete section
#     client.delete(f"/api/sections/{section['id']}")
#
#     # Verify cards are gone
#     cards = client.get("/api/cards").json()
#     assert len(cards) == 0
