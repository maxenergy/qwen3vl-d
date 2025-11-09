"""Integration tests for projects API."""

import pytest
from fastapi.testclient import TestClient


class TestProjectsAPI:
    """Test projects API endpoints."""

    def test_create_project(self, client: TestClient, sample_project_data):
        """Test creating a new project."""
        response = client.post("/api/v1/projects", json=sample_project_data)

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == sample_project_data["name"]
        assert data["description"] == sample_project_data["description"]
        assert "id" in data
        assert "created_at" in data
        assert len(data.get("labels", [])) == 2

    def test_create_project_invalid_data(self, client: TestClient):
        """Test creating project with invalid data."""
        invalid_data = {}  # Missing required field 'name'

        response = client.post("/api/v1/projects", json=invalid_data)

        assert response.status_code == 422  # Validation error

    def test_list_projects(self, client: TestClient, sample_project_data):
        """Test listing projects."""
        # Create a project first
        client.post("/api/v1/projects", json=sample_project_data)

        # List projects
        response = client.get("/api/v1/projects")

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert data["total"] >= 1

    def test_get_project(self, client: TestClient, sample_project_data):
        """Test getting a specific project."""
        # Create project
        create_response = client.post("/api/v1/projects", json=sample_project_data)
        project_id = create_response.json()["id"]

        # Get project
        response = client.get(f"/api/v1/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == project_id
        assert data["name"] == sample_project_data["name"]

    def test_get_project_not_found(self, client: TestClient):
        """Test getting non-existent project."""
        response = client.get("/api/v1/projects/99999")

        assert response.status_code == 404

    def test_update_project(self, client: TestClient, sample_project_data):
        """Test updating a project."""
        # Create project
        create_response = client.post("/api/v1/projects", json=sample_project_data)
        project_id = create_response.json()["id"]

        # Update project
        update_data = {"name": "Updated Project Name"}
        response = client.patch(f"/api/v1/projects/{project_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "Updated Project Name"

    def test_delete_project(self, client: TestClient, sample_project_data):
        """Test deleting a project."""
        # Create project
        create_response = client.post("/api/v1/projects", json=sample_project_data)
        project_id = create_response.json()["id"]

        # Delete project
        response = client.delete(f"/api/v1/projects/{project_id}")

        assert response.status_code == 200

        # Verify deletion
        get_response = client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404

    def test_add_label_to_project(self, client: TestClient, sample_project_data):
        """Test adding a label to a project."""
        # Create project
        create_response = client.post("/api/v1/projects", json=sample_project_data)
        project_id = create_response.json()["id"]

        # Add label
        label_data = {"name": "bicycle", "color": "#0000FF"}
        response = client.post(
            f"/api/v1/projects/{project_id}/labels",
            json=label_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "bicycle"
        assert data["color"] == "#0000FF"

    def test_pagination(self, client: TestClient, sample_project_data):
        """Test project list pagination."""
        # Create multiple projects
        for i in range(5):
            data = sample_project_data.copy()
            data["name"] = f"Project {i}"
            client.post("/api/v1/projects", json=data)

        # Test pagination
        response = client.get("/api/v1/projects?page=1&per_page=2")

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) <= 2
        assert data["page"] == 1
        assert data["per_page"] == 2


class TestProjectLabels:
    """Test project labels functionality."""

    def test_create_project_with_labels(self, client: TestClient):
        """Test creating project with initial labels."""
        project_data = {
            "name": "Label Test Project",
            "description": "Test project for labels",
            "labels": [
                {"name": "car", "color": "#FF0000"},
                {"name": "truck", "color": "#00FF00"}
            ]
        }

        response = client.post("/api/v1/projects", json=project_data)

        assert response.status_code == 200
        data = response.json()

        assert len(data["labels"]) == 2
        assert data["labels"][0]["name"] == "car"

    def test_update_label(self, client: TestClient, sample_project_data):
        """Test updating a label."""
        # Create project with labels
        create_response = client.post("/api/v1/projects", json=sample_project_data)
        project_id = create_response.json()["id"]
        label_id = create_response.json()["labels"][0]["id"]

        # Update label
        update_data = {"name": "updated_car", "color": "#FFFF00"}
        response = client.patch(
            f"/api/v1/projects/{project_id}/labels/{label_id}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "updated_car"
        assert data["color"] == "#FFFF00"

    def test_delete_label(self, client: TestClient, sample_project_data):
        """Test deleting a label."""
        # Create project
        create_response = client.post("/api/v1/projects", json=sample_project_data)
        project_id = create_response.json()["id"]
        label_id = create_response.json()["labels"][0]["id"]

        # Delete label
        response = client.delete(
            f"/api/v1/projects/{project_id}/labels/{label_id}"
        )

        assert response.status_code == 200

        # Verify project still exists with fewer labels
        project_response = client.get(f"/api/v1/projects/{project_id}")
        assert len(project_response.json()["labels"]) == 1


class TestProjectStatistics:
    """Test project statistics."""

    def test_get_project_statistics(self, client: TestClient, sample_project_data):
        """Test getting project statistics."""
        # Create project
        create_response = client.post("/api/v1/projects", json=sample_project_data)
        project_id = create_response.json()["id"]

        # Get statistics
        response = client.get(f"/api/v1/projects/{project_id}/statistics")

        assert response.status_code == 200
        data = response.json()

        # Should have stats fields
        assert "image_count" in data
        assert "annotation_count" in data
        assert "dataset_count" in data
