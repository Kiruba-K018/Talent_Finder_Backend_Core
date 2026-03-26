import uuid
from datetime import datetime

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.data.clients.postgres_client import Base


class Role(Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())


class Permission(Base):
    __tablename__ = "permissions"

    permission_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True
    )
    entity_name: Mapped[str] = mapped_column(String, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)


class RolePermissionMap(Base):
    __tablename__ = "role_permission_map"

    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.role_id"), primary_key=True
    )
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("permissions.permission_id"), primary_key=True
    )


class Organization(Base):
    __tablename__ = "organizations"

    org_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    org_name: Mapped[str] = mapped_column(String, nullable=False)
    org_logo: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    role_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("roles.role_id"), nullable=True
    )
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    org_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.org_id"), nullable=True
    )
    created_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    jti: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=True
    )
    is_rotated: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_jti: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )
    rotated_at: Mapped[datetime | None] = mapped_column(TIMESTAMP, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    jti: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("refresh_tokens.jti"), primary_key=True
    )
    revoked_at: Mapped[datetime] = mapped_column(TIMESTAMP, default=func.now())
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=False)
