from dataclasses import dataclass
from datetime import datetime
from flask_login import UserMixin # type: ignore

from flask_sqlalchemy import SQLAlchemy # type: ignore
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import relationship

db = SQLAlchemy()

@dataclass
class Submission(db.Model): # type: ignore
    __tablename__ = 'submissions'

    id: int = db.Column(Integer, primary_key=True, autoincrement=True)
    assignment_id: int = db.Column(Integer, ForeignKey('assignments.id'), nullable=False)
    student_id: str = db.Column(Text, ForeignKey('students.username'), nullable=False)
    code: str = db.Column(Text, nullable=False)
    grade: int = db.Column(Integer, nullable=False)
    time: datetime = db.Column(DateTime, server_default=func.now(), nullable=False)

@dataclass
class Student(db.Model, UserMixin): # type: ignore
    __tablename__ = 'students'

    username: str = db.Column(Text, primary_key=True, nullable=False)
    hashed_pw: str = db.Column(Text, nullable=False)
    grade: int = db.Column(Integer, nullable=False)
    submissions: relationship = relationship(Submission)

    def get_id(self):
        return self.username

@dataclass
class Assignment(db.Model): # type: ignore
    __tablename__ = 'assignments'

    id: int = db.Column(Integer, primary_key=True, autoincrement=True)
    title: str = db.Column(Text, nullable=False)
    description: str = db.Column(Text, nullable=False)
    starting_code: str = db.Column(Text, nullable=False)
    due: str = db.Column(Text, nullable=False)
    open: bool = db.Column(Boolean, nullable=False)
    submissions: relationship = relationship(Submission)

def init_database() -> None:
    db.create_all()
    db.session.merge(Student(
        username='debug',
        hashed_pw='',
        grade=0,
    ))
    db.session.merge(Assignment(
        id=1,
        title='Add two numbers',
        description='Write a function called "add" which adds two numbers.',
        starting_code='def add(a, b):\n    a = 1\n    return b + 1',
        due='August 2',
        open=False,
    ))
    db.session.merge(Assignment(
        id=2,
        title='Print a list',
        description='Write a function called "print_list" which prints out each value in a list.',
        starting_code='def print_list(x):\n    return x[0] + x[1] + x[2]',
        due='August 9',
        open=False,
    ))
    db.session.merge(Assignment(
        id=3,
        title='Read a dictionary',
        description='Write a function called "get_height" which takes a dictionary with strings as keys, and returns the value of the key "height".',
        starting_code='def get_height(x):\n    return x["hieght"]',
        due='August 16',
        open=False,
    ))
    db.session.merge(Assignment(
        id=4,
        title='Calculate max',
        description='Write a function called "find_max" which takes a list and returns the largest value.',
        starting_code='def find_max(x):\n    return x',
        due='September 7',
        open=True,
    ))

    db.session.commit()
