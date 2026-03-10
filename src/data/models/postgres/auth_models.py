from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.data.clients.postgres_client import Base


class Role(Base):
    __tablename__ = "roles"

    role_id = Column(Integer, primary_key=True, autoincrement=True)
    role = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())


class Permission(Base):
    __tablename__ = "permissions"

    permission_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_name = Column(String, nullable=False)
    action = Column(String, nullable=False)


class RolePermissionMap(Base):
    __tablename__ = "role_permission_map"

    role_id = Column(Integer, ForeignKey("roles.role_id"), primary_key=True)
    permission_id = Column(
        Integer, ForeignKey("permissions.permission_id"), primary_key=True
    )


class Organization(Base):
    __tablename__ = "organizations"

    org_id = Column(UUID(as_uuid=True), primary_key=True)
    org_name = Column(String, nullable=False)
    org_logo = Column(String)
    created_at = Column(TIMESTAMP, default=func.now())


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String, nullable=False, unique=True)
    hashed_password = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.role_id"))
    name = Column(String)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.org_id"))
    created_at = Column(TIMESTAMP)
    updated_at = Column(TIMESTAMP)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    jti = Column(UUID(as_uuid=True), primary_key=True)
    session_id = Column(UUID(as_uuid=True), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    is_rotated = Column(Boolean, default=False)
    parent_jti = Column(UUID(as_uuid=True))
    rotated_at = Column(TIMESTAMP)
    expires_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    jti = Column(UUID(as_uuid=True), ForeignKey("refresh_tokens.jti"), primary_key=True)
    revoked_at = Column(TIMESTAMP, default=func.now())
    expires_at = Column(TIMESTAMP, nullable=False)
