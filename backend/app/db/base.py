from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    SQLAlchemy 2.0 Declarative Base with typed metadata inspection.
    All ORM entity models inherit from this base class.
    """
    pass
