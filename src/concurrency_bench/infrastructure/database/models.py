from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from concurrency_lab.infrastructure.database.base import Base


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)


class PurchaseModel(Base):
    __tablename__ = "purchases"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    product_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class ExperimentModel(Base):
    __tablename__ = "experiments"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    experiment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    task_count: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    parameters_json: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    results: Mapped[list[ExperimentResultModel]] = relationship(
        "ExperimentResultModel",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )


class ExperimentResultModel(Base):
    __tablename__ = "experiment_results"

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    experiment_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
    )
    strategy: Mapped[str] = mapped_column(String(50), nullable=False)
    completed_task_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_time_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    cpu_usage_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    memory_usage_mb: Mapped[float | None] = mapped_column(Float, nullable=True)
    workers_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
    speedup: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[str] = mapped_column(String, nullable=False)

    experiment: Mapped[ExperimentModel] = relationship(
        "ExperimentModel",
        back_populates="results",
    )
