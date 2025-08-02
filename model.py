from typing import List
from sqlalchemy import String, Date
from sqlalchemy import ForeignKey
from sqlalchemy import Table, Column
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
import datetime

class Base(DeclarativeBase):
    pass

group_membership = Table(
    "group_membership",
    Base.metadata,
    Column("group_id", ForeignKey("group.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", ForeignKey("user.id", ondelete="CASCADE"), primary_key=True),
)

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(30), nullable=False)
    last_name: Mapped[str] = mapped_column(String(30), nullable=False)

    groups: Mapped[List["Group"]] = relationship(
        secondary=group_membership,
        back_populates="members",
        cascade="all",
        passive_deletes=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name
        }

class Expense(Base):
    __tablename__ = "expense"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    totalCost: Mapped[float] = mapped_column(nullable=False)
    paid_by_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    payer_portion: Mapped[float] = mapped_column(nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id", ondelete="CASCADE"), nullable=False)

    paid_by: Mapped["User"] = relationship()
    group: Mapped["Group"] = relationship(back_populates="expenses")
    splits: Mapped[List["ExpenseSplit"]] = relationship(
        back_populates="expense",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "date": self.date.isoformat(),
            "totalCost": self.totalCost,
            "paid_by_id": self.paid_by_id,
            "payer_portion": self.payer_portion,
            "group_id": self.group_id,
            "paid_by": self.paid_by.to_dict() if self.paid_by else None,
            "group": self.group.name if self.group else None,
            "splits": [split.to_dict() for split in self.splits]
        }
    
class ExpenseSplit(Base):
    __tablename__ = "expense_split"
    user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"), primary_key=True, nullable=True
    )
    expense_id: Mapped[int] = mapped_column(ForeignKey("expense.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    amount_paid: Mapped[float] = mapped_column(nullable=False)
    amount_owed: Mapped[float] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship()
    expense: Mapped["Expense"] = relationship(back_populates="splits")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "amount_paid": self.amount_paid,
            "amount_owed": self.amount_owed,
            "user": self.user.to_dict() if self.user else None
        }
    
class Group(Base):
    __tablename__ = "group"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    
    owner: Mapped["User"] = relationship(passive_deletes=True)
    members: Mapped[List["User"]] = relationship(
        secondary=group_membership,
        back_populates="groups",
        passive_deletes=True
    )
    expenses: Mapped[List["Expense"]] = relationship(
        back_populates="group",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "owner_id": self.owner_id,
            "owner": self.owner.to_dict(),
            "members": [member.to_dict() for member in self.members],
            "expenses": [expense.to_dict() for expense in self.expenses]
        }
