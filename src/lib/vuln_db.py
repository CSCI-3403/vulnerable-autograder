from pathlib import Path
import sqlite3


class VulnDB:
    def __init__(self, path: Path, student: str):
        # need_init = not path.isfile()

        self.student = student
        self.connection = sqlite3.connect(path)

        # if need_init:
        #    self.init()

    def init(self):
        cur = self.connection.cursor()

        cur.execute('DROP TABLE IF EXISTS grades')
        cur.execute('CREATE TABLE grades (student TEXT, assignment INT, score INT)')

        cur.executemany('INSERT INTO grades VALUES (?, ?, ?)',[
            (self.student, 1, 0),
            (self.student, 2, 0),
            (self.student, 3, 0),
            (self.student, 4, 0),
            ('Alice', 1, 100),
            ('Alice', 2, 90),
            ('Alice', 3, 100),
            ('Alice', 4, 100),
            ('Bob', 1, 80),
            ('Bob', 2, 70),
            ('Bob', 3, 100),
            ('Bob', 4, 80),
        ])

        self.connection.commit()
    
    def read_grade(self, assignment: int):
        cur = self.connection.cursor()

        res = cur.execute('SELECT score FROM grades WHERE student=? AND assignment=?', (self.student, assignment)).fetchone()

        if res is not None:
            return res[0]
        else:
            return 0

    def read_grades(self):
        cur = self.connection.cursor()

        scores = cur.execute('SELECT assignment, score FROM grades WHERE student=?', (self.student,))

        return {assignment: score for (assignment, score) in scores.fetchall()}
