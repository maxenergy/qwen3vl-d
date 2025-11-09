"""API client for CLI to interact with backend."""

import os
import requests
from typing import Dict, Any, Optional, List
from urllib.parse import urljoin


class APIClient:
    """Client for communicating with the Auto-Annotation API."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = 30):
        """
        Initialize API client.

        Args:
            base_url: Base URL for API (defaults to env var or localhost)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv('API_BASE_URL', 'http://localhost:8000')
        self.timeout = timeout
        self.session = requests.Session()

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        files: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to API."""
        url = urljoin(self.base_url, f'/api{endpoint}')

        try:
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json,
                files=files,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API request failed: {e}")

    # Projects
    def list_projects(self, page: int = 1, per_page: int = 20) -> Dict:
        """List all projects."""
        return self._request('GET', '/projects', params={'page': page, 'per_page': per_page})

    def get_project(self, project_id: int) -> Dict:
        """Get project details."""
        return self._request('GET', f'/projects/{project_id}')

    def create_project(self, name: str, description: str = '', labels: List[Dict] = None) -> Dict:
        """Create a new project."""
        data = {'name': name, 'description': description}
        if labels:
            data['labels'] = labels
        return self._request('POST', '/projects', json=data)

    def update_project(self, project_id: int, **kwargs) -> Dict:
        """Update project."""
        return self._request('PATCH', f'/projects/{project_id}', json=kwargs)

    def delete_project(self, project_id: int) -> Dict:
        """Delete project."""
        return self._request('DELETE', f'/projects/{project_id}')

    # Labels
    def add_label(self, project_id: int, name: str, color: str = '#1890ff') -> Dict:
        """Add label to project."""
        return self._request('POST', f'/projects/{project_id}/labels',
                           json={'name': name, 'color': color})

    # Generation
    def list_generation_tasks(self, project_id: int, page: int = 1) -> Dict:
        """List generation tasks."""
        return self._request('GET', f'/projects/{project_id}/generation/tasks',
                           params={'page': page})

    def create_generation_task(self, project_id: int, **kwargs) -> Dict:
        """Create generation task."""
        return self._request('POST', f'/projects/{project_id}/generation/tasks', json=kwargs)

    def get_generation_task(self, project_id: int, task_id: int) -> Dict:
        """Get generation task details."""
        return self._request('GET', f'/projects/{project_id}/generation/tasks/{task_id}')

    # Images
    def list_images(self, project_id: int, page: int = 1, **filters) -> Dict:
        """List images."""
        params = {'page': page, **filters}
        return self._request('GET', f'/projects/{project_id}/images', params=params)

    def review_image(self, project_id: int, image_id: int, approved: bool, notes: str = '') -> Dict:
        """Review an image."""
        return self._request('PATCH', f'/projects/{project_id}/images/{image_id}/review',
                           json={'approved': approved, 'notes': notes})

    # Annotation
    def list_annotation_tasks(self, project_id: int, page: int = 1) -> Dict:
        """List annotation tasks."""
        return self._request('GET', f'/projects/{project_id}/annotation/tasks',
                           params={'page': page})

    def create_annotation_task(self, project_id: int, **kwargs) -> Dict:
        """Create annotation task."""
        return self._request('POST', f'/projects/{project_id}/annotation/tasks', json=kwargs)

    def get_annotation_task(self, project_id: int, task_id: int) -> Dict:
        """Get annotation task details."""
        return self._request('GET', f'/projects/{project_id}/annotation/tasks/{task_id}')

    def get_annotation_statistics(self, project_id: int) -> Dict:
        """Get annotation statistics."""
        return self._request('GET', f'/projects/{project_id}/annotations/statistics')

    # Datasets
    def list_datasets(self, project_id: int, page: int = 1) -> Dict:
        """List dataset versions."""
        return self._request('GET', f'/projects/{project_id}/datasets',
                           params={'page': page})

    def create_dataset(self, project_id: int, **kwargs) -> Dict:
        """Create dataset version."""
        return self._request('POST', f'/projects/{project_id}/datasets', json=kwargs)

    def get_dataset(self, project_id: int, dataset_id: int) -> Dict:
        """Get dataset details."""
        return self._request('GET', f'/projects/{project_id}/datasets/{dataset_id}')

    def export_dataset(self, project_id: int, dataset_id: int, format: str) -> Dict:
        """Export dataset."""
        return self._request('POST', f'/projects/{project_id}/datasets/{dataset_id}/export',
                           json={'format': format})

    # Training
    def list_training_tasks(self, project_id: int, page: int = 1) -> Dict:
        """List training tasks."""
        return self._request('GET', f'/projects/{project_id}/training/tasks',
                           params={'page': page})

    def create_training_task(self, project_id: int, **kwargs) -> Dict:
        """Create training task."""
        return self._request('POST', f'/projects/{project_id}/training/tasks', json=kwargs)

    def get_training_task(self, project_id: int, task_id: int) -> Dict:
        """Get training task details."""
        return self._request('GET', f'/projects/{project_id}/training/tasks/{task_id}')

    def stop_training_task(self, project_id: int, task_id: int) -> Dict:
        """Stop training task."""
        return self._request('POST', f'/projects/{project_id}/training/tasks/{task_id}/stop')

    # Models
    def list_models(self, project_id: int, page: int = 1) -> Dict:
        """List trained models."""
        return self._request('GET', f'/projects/{project_id}/models',
                           params={'page': page})

    def get_model(self, project_id: int, model_id: int) -> Dict:
        """Get model details."""
        return self._request('GET', f'/projects/{project_id}/models/{model_id}')
