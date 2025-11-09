# Authentication & Authorization Guide

Complete guide for user authentication and role-based access control (RBAC).

## Overview

The system uses JWT (JSON Web Tokens) for authentication and role-based access control (RBAC) for authorization.

## Features

✅ **JWT Authentication** - Secure token-based authentication
✅ **Role-Based Access Control** - Fine-grained permissions
✅ **Password Hashing** - Bcrypt password encryption
✅ **Token Refresh** - Long-lived refresh tokens
✅ **Permission System** - Resource-action based permissions

## User Roles

### Default Roles

1. **admin** - Full system access
   - All permissions (*)

2. **user** (default) - Standard user access
   - project:read, project:write
   - image:read, image:write
   - annotation:read, annotation:write
   - dataset:read, dataset:write
   - training:read, training:write

3. **viewer** - Read-only access
   - project:read
   - image:read
   - annotation:read
   - dataset:read
   - training:read

4. **annotator** - Annotation-focused
   - project:read
   - image:read
   - annotation:read, annotation:write

## API Endpoints

### Register
```bash
POST /api/v1/auth/register

Request:
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "securepass123",
  "full_name": "John Doe"
}

Response:
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "roles": ["user"],
  "permissions": ["project:read", "project:write", ...],
  "created_at": "2024-01-01T00:00:00"
}
```

### Login
```bash
POST /api/v1/auth/login

Request:
{
  "username": "john_doe",
  "password": "securepass123"
}

Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Get Current User
```bash
GET /api/v1/auth/me
Authorization: Bearer <access_token>

Response:
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "roles": ["user"],
  "permissions": ["project:read", ...],
  ...
}
```

## Usage Examples

### Python Client
```python
import requests

BASE_URL = "http://localhost:8000"

# Register
response = requests.post(f"{BASE_URL}/api/v1/auth/register", json={
    "username": "john_doe",
    "email": "john@example.com",
    "password": "securepass123"
})
user = response.json()

# Login
response = requests.post(f"{BASE_URL}/api/v1/auth/login", json={
    "username": "john_doe",
    "password": "securepass123"
})
tokens = response.json()
access_token = tokens["access_token"]

# Make authenticated request
headers = {"Authorization": f"Bearer {access_token}"}
response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
```

### FastAPI Endpoint with Auth
```python
from fastapi import Depends, APIRouter
from backend.core.auth import get_current_user, require_permission
from backend.models.user import User

router = APIRouter()

# Require authentication
@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Hello {current_user.username}"}

# Require specific permission
@router.post("/projects")
async def create_project(
    current_user: User = Depends(require_permission("project:write"))
):
    return {"message": "Project created"}

# Require superuser
from backend.core.auth import require_superuser

@router.get("/admin")
async def admin_route(current_user: User = Depends(require_superuser)):
    return {"message": "Admin access"}
```

## Permission System

### Permission Format
`resource:action`

Examples:
- `project:read` - View projects
- `project:write` - Create/update projects
- `annotation:delete` - Delete annotations

### Available Permissions
- **project**: read, write, delete
- **image**: read, write, delete
- **annotation**: read, write, delete
- **dataset**: read, write, delete
- **training**: read, write, delete
- **user**: read, write, delete (admin only)
- **system**: admin (superuser only)

## Security Best Practices

1. **Strong Passwords** - Minimum 8 characters
2. **Token Storage** - Store tokens securely (httpOnly cookies recommended)
3. **Token Expiry** - Access tokens expire in 30 minutes
4. **HTTPS Only** - Always use HTTPS in production
5. **Rate Limiting** - Implement rate limiting on auth endpoints

## Database Schema

### Users Table
- id, username, email, hashed_password
- status, is_active, is_superuser, is_verified
- created_at, updated_at, last_login_at

### Roles Table
- id, name, description, is_default

### Permissions Table
- id, name, description, resource, action

### Relationships
- User ←→ Role (many-to-many)
- Role ←→ Permission (many-to-many)

## Initialization

The system automatically creates default roles and permissions on startup:

```python
from backend.models.user import init_default_roles_and_permissions

# In your startup code
with SessionLocal() as db:
    init_default_roles_and_permissions(db)
```

## Further Reading

- [JWT Documentation](https://jwt.io/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [RBAC Concepts](https://en.wikipedia.org/wiki/Role-based_access_control)
