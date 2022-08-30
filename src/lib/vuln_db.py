from pathlib import Path
import sqlite3


class VulnDB:
    def __init__(self, path: Path, student: str):
        self.student = student
        self.connection = sqlite3.connect(path)
    
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
