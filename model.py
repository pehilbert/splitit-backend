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
    Column("group_id", ForeignKey("group.id"), primary_key=True),
    Column("user_id", ForeignKey("user.id"), primary_key=True),
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
        back_populates="members"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "firstName": self.first_name,
            "lastName": self.last_name
        }

class Expense(Base):
    __tablename__ = "expense"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    date: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    totalCost: Mapped[float] = mapped_column(nullable=False)
    paid_by_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    payer_portion: Mapped[float] = mapped_column(nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("group.id"), nullable=False)

    paid_by: Mapped["User"] = relationship()
    group: Mapped["Group"] = relationship(back_populates="expenses")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "date": self.date.isoformat(),
            "totalCost": self.totalCost,
            "paidById": self.paid_by_id,
            "payerPortion": self.payer_portion,
            "groupId": self.group_id,
            "paidBy": self.paid_by.to_dict() if self.paid_by else None,
            "group": self.group.name if self.group else None
        }
    
class ExpenseSplit(Base):
    __tablename__ = "expense_split"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    amount_paid: Mapped[float] = mapped_column(nullable=False)
    amount_owed: Mapped[float] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship()

    def to_dict(self):
        return {
            "id": self.id,
            "userId": self.user_id,
            "amountPaid": self.amount_paid,
            "amountOwed": self.amount_owed,
            "user": self.user.to_dict() if self.user else None
        }
    
class Group(Base):
    __tablename__ = "group"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    
    owner: Mapped["User"] = relationship()
    members: Mapped[List["User"]] = relationship(
        secondary=group_membership,
        back_populates="groups"
    )
    expenses: Mapped[List["Expense"]] = relationship(
        back_populates="group"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "ownerId": self.owner_id,
            "owner": self.owner.to_dict() if self.owner else None,
            "members": [member.to_dict() for member in self.members],
            "expenses": [expense.to_dict() for expense in self.expenses]
        }   
