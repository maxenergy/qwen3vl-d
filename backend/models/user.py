"""User and authentication models.

This module defines user, role, and permission models for
authentication and authorization.
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import List

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Table, Enum
from sqlalchemy.orm import relationship

from backend.core.database import Base


# Association table for user-role many-to-many relationship
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete='CASCADE')),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE'))
)

# Association table for role-permission many-to-many relationship
role_permissions = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id', ondelete='CASCADE')),
    Column('permission_id', Integer, ForeignKey('permissions.id', ondelete='CASCADE'))
)


class UserStatus(str, PyEnum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))

    # Status and flags
    status = Column(Enum(UserStatus), default=UserStatus.PENDING, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)

    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"

    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role."""
        return any(role.name == role_name for role in self.roles)

    def has_permission(self, permission_name: str) -> bool:
        """Check if user has a specific permission."""
        if self.is_superuser:
            return True

        for role in self.roles:
            if any(perm.name == permission_name for perm in role.permissions):
                return True
        return False

    def get_permissions(self) -> List[str]:
        """Get all permissions for this user."""
        if self.is_superuser:
            return ["*"]  # Superuser has all permissions

        permissions = set()
        for role in self.roles:
            for perm in role.permissions:
                permissions.add(perm.name)
        return list(permissions)


class Role(Base):
    """Role model for RBAC."""

    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255))
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")

    def __repr__(self):
        return f"<Role(id={self.id}, name={self.name})>"


class Permission(Base):
    """Permission model for fine-grained access control."""

    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255))
    resource = Column(String(50))  # e.g., "project", "image", "dataset"
    action = Column(String(50))    # e.g., "read", "write", "delete"

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

    def __repr__(self):
        return f"<Permission(id={self.id}, name={self.name})>"


# Default roles and permissions
DEFAULT_ROLES = [
    {
        "name": "admin",
        "description": "Administrator with full access",
        "permissions": ["*"]
    },
    {
        "name": "user",
        "description": "Regular user with standard access",
        "permissions": [
            "project:read", "project:write",
            "image:read", "image:write",
            "annotation:read", "annotation:write",
            "dataset:read", "dataset:write",
            "training:read", "training:write"
        ],
        "is_default": True
    },
    {
        "name": "viewer",
        "description": "Read-only access",
        "permissions": [
            "project:read",
            "image:read",
            "annotation:read",
            "dataset:read",
            "training:read"
        ]
    },
    {
        "name": "annotator",
        "description": "Can annotate images",
        "permissions": [
            "project:read",
            "image:read",
            "annotation:read", "annotation:write"
        ]
    }
]

DEFAULT_PERMISSIONS = [
    # Project permissions
    {"name": "project:read", "resource": "project", "action": "read", "description": "View projects"},
    {"name": "project:write", "resource": "project", "action": "write", "description": "Create/update projects"},
    {"name": "project:delete", "resource": "project", "action": "delete", "description": "Delete projects"},

    # Image permissions
    {"name": "image:read", "resource": "image", "action": "read", "description": "View images"},
    {"name": "image:write", "resource": "image", "action": "write", "description": "Upload/update images"},
    {"name": "image:delete", "resource": "image", "action": "delete", "description": "Delete images"},

    # Annotation permissions
    {"name": "annotation:read", "resource": "annotation", "action": "read", "description": "View annotations"},
    {"name": "annotation:write", "resource": "annotation", "action": "write", "description": "Create/update annotations"},
    {"name": "annotation:delete", "resource": "annotation", "action": "delete", "description": "Delete annotations"},

    # Dataset permissions
    {"name": "dataset:read", "resource": "dataset", "action": "read", "description": "View datasets"},
    {"name": "dataset:write", "resource": "dataset", "action": "write", "description": "Create/update datasets"},
    {"name": "dataset:delete", "resource": "dataset", "action": "delete", "description": "Delete datasets"},

    # Training permissions
    {"name": "training:read", "resource": "training", "action": "read", "description": "View training jobs"},
    {"name": "training:write", "resource": "training", "action": "write", "description": "Create training jobs"},
    {"name": "training:delete", "resource": "training", "action": "delete", "description": "Delete training jobs"},

    # User management permissions
    {"name": "user:read", "resource": "user", "action": "read", "description": "View users"},
    {"name": "user:write", "resource": "user", "action": "write", "description": "Create/update users"},
    {"name": "user:delete", "resource": "user", "action": "delete", "description": "Delete users"},

    # System permissions
    {"name": "system:admin", "resource": "system", "action": "admin", "description": "System administration"},
]


def init_default_roles_and_permissions(db):
    """Initialize default roles and permissions.

    Args:
        db: Database session
    """
    from backend.core.logging import logger

    try:
        # Create permissions
        permission_map = {}
        for perm_data in DEFAULT_PERMISSIONS:
            perm = db.query(Permission).filter(Permission.name == perm_data["name"]).first()
            if not perm:
                perm = Permission(**perm_data)
                db.add(perm)
                db.flush()
                logger.info(f"Created permission: {perm.name}")
            permission_map[perm.name] = perm

        # Create wildcard permission for admins
        wildcard_perm = db.query(Permission).filter(Permission.name == "*").first()
        if not wildcard_perm:
            wildcard_perm = Permission(
                name="*",
                description="All permissions",
                resource="*",
                action="*"
            )
            db.add(wildcard_perm)
            db.flush()
            permission_map["*"] = wildcard_perm

        # Create roles
        for role_data in DEFAULT_ROLES:
            role = db.query(Role).filter(Role.name == role_data["name"]).first()
            if not role:
                role = Role(
                    name=role_data["name"],
                    description=role_data["description"],
                    is_default=role_data.get("is_default", False)
                )
                db.add(role)
                db.flush()

                # Add permissions to role
                for perm_name in role_data["permissions"]:
                    if perm_name in permission_map:
                        role.permissions.append(permission_map[perm_name])

                logger.info(f"Created role: {role.name} with {len(role.permissions)} permissions")

        db.commit()
        logger.info("Default roles and permissions initialized successfully")

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to initialize roles and permissions: {e}")
        raise
