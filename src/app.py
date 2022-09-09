from functools import lru_cache
import logging
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple, Union

import click
from flask import abort, Flask, jsonify, render_template, request, redirect, url_for
from flask_bcrypt import Bcrypt # type: ignore
from flask_login import current_user, LoginManager, login_required, login_user, logout_user # type: ignore
from flask_wtf import FlaskForm # type: ignore
from werkzeug.wrappers import Response
from wtforms import StringField, PasswordField, SubmitField # type: ignore
from wtforms.validators import DataRequired # type: ignore

from lib.models import Assignment, Submission, db, init_database, Student
from lib.vuln_db import VulnDB

GRADING_TEMPLATE = Path("lib", "template.py").read_text()
VALID_USERS_FILE = Path("secrets", "valid_users.txt")
View = Union[Response, str, Tuple[str, int]]

# Init logging
log = logging.getLogger(__name__)
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

app = Flask(__name__)
app.secret_key = Path("secrets", "secret_key.txt").read_text()

bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

app.config.update(
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_DATABASE_URI="sqlite:///grading.sqlite3",
    student_root="/home",
)

db.init_app(app)
with app.app_context():
    init_database()

@login_manager.user_loader
def load_user(username):
    return db.session.query(Student).filter(Student.username == username).first()

@app.context_processor
def inject_context():
    return {
        "assignments": get_assignments()
    }

def get_insecure_db(user: str):
    return VulnDB(Path(app.config["student_root"], user, "database.sqlite3"), user)

@lru_cache()
def get_assignments():
    return db.session.query(Assignment).all()

def run_as_user(path: Path, user: str):
    log.info(f"Running process as user: {user}")
    if os.name != "posix":
        log.warning("Cannot demote subprocess outside of a Posix system")
        preexec_fn = None
        env = None
    else:
        import pwd

        pw_record = pwd.getpwnam(user)
        sgid = os.getgrouplist(user, pw_record.pw_gid)
        log.info(f"Demoting to user: {pw_record.pw_name} (ID: {pw_record.pw_uid})")
        preexec_fn = demote_process(pw_record.pw_uid, pw_record.pw_gid, sgid)

        env = os.environ.copy()
        env.update({
            "HOME": pw_record.pw_dir,
            "LOGNAME": pw_record.pw_name,
            "USER": pw_record.pw_name,
            "SHELL": pw_record.pw_shell,
        })

    result = subprocess.Popen(
        ["python", path.name],
        cwd=path.parent,
        preexec_fn=preexec_fn,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        )

    try:
        output, error = result.communicate(timeout=2)
    except:
        log.exception("Exception waiting for communication")
        result.kill()
        output = b''
        error = b'Program timed out'

    # output = result.stdout.read().decode() # type: ignore
    # error = result.stderr.read().decode() # type: ignore

    try:
        return output.decode(), error.decode()
    except:
        return '', 'Unable to decode output'

def demote_process(uid: int, gid: int, sgids: List[int]):
    def ret():
        os.setgid(gid)
        os.setgroups(sgids)
        os.setuid(uid)
    return ret

@app.route("/")
@login_required
def index():
    scores = get_insecure_db(current_user.username).read_grades()
    return render_template("index.html", scores=scores)

@app.route("/grades")
@login_required
def grades():
    scores = get_insecure_db(current_user.username).read_grades()
    average = sum(scores.values()) / len(scores)
    return render_template("grades.html", scores=scores, average=average)

@app.route("/assignments/<assignment_id>")
@login_required
def assignment(assignment_id: int):
    assignment = db.session.query(Assignment).filter(Assignment.id==assignment_id).first()
    submission = (db.session.query(Submission)
        .filter(Submission.student_id==current_user.username)
        .filter(Submission.assignment_id==assignment_id)
        .order_by(Submission.id.desc())
        .first())
    score = get_insecure_db(current_user.username).read_grade(assignment_id)
    return render_template("assignment.html", assignment=assignment, submission=submission, score=score)

@app.route("/submit/<assignment_id>", methods=["POST"])
@login_required
def submit(assignment_id: int):
    assignment = db.session.query(Assignment).filter(Assignment.id==assignment_id).first()
    if not assignment.open:
        abort(403)

    code = request.data.decode()

    try:
        grading_script = GRADING_TEMPLATE.format(
            student_code=code,
            student=current_user.username,
            assignment=assignment_id)

        script_path = Path(app.config["student_root"], current_user.username, "grading_script.py")
        script_path.write_text(grading_script)

        output, error = run_as_user(script_path, current_user.username)

        vuln_db = get_insecure_db(current_user.username)

        score = vuln_db.read_grade(assignment_id)

        all_grades = vuln_db.read_grades()
        average_grade = sum(all_grades.values()) / len(all_grades)
    except:
        log.exception("Error while grading")
        output = ''
        error = 'Server error: Please tell the teaching team about this'
        score = 0
        average_grade = 0

    db.session.add(Submission(assignment_id=assignment_id, student_id=current_user.username, code=code, grade=average_grade))
    db.session.commit()

    return jsonify({
        "output": output,
        "error": error,
        "score": score,
    })

class LoginForm(FlaskForm):
    username  = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign In")
    create = SubmitField("Create Account")

@app.route("/login", methods=["GET", "POST"])
def login():
    if app.debug:
        login_user(Student(username="debug"))
        log.info("Automatically logging in as debug user")
        return redirect(url_for("index"))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        pw = form.password.data

        student = db.session.query(Student).filter(Student.username == username).first()

        if username not in VALID_USERS_FILE.read_text().split():
            log.info(f"Not in user allowlist: '{username}'")
            form.username.errors.append("Invalid username (please use your identikey)")
        elif form.create.data:
            if not student:
                hashed_pw = bcrypt.generate_password_hash(pw)

                student = Student(username=username, hashed_pw=hashed_pw, grade=0)
                db.session.add(student)
                db.session.commit()

                login_user(student)
                log.info(f"User successfully created: {username}")
                return redirect(url_for("index"))
            else:
                log.info(f"Failed to recreate user: {username}")
                form.username.errors.append("This username is already taken")
        else:
            student = db.session.query(Student).filter(Student.username == username).first()

            #if student and bcrypt.check_password_hash(student.hashed_pw, pw):
            if student and (bcrypt.check_password_hash(student.hashed_pw, pw) or (current_user.is_authenticated and current_user.username == "admin")):
                login_user(student)
                log.info(f"Logged in: {username}")
                return redirect(url_for("index"))
            elif not student:
                log.info(f"Invalid user: {username}")
                form.username.errors.append("No user with this username")
            else:
                log.info(f"Invalid password for: {username}")
                form.password.errors.append("Incorrect password")

    return render_template("login.html", form=form)

@app.route("/logout")
def logout() -> View:
    # I know, I know, this is vulnerable to CSRF. They won't care.
    logout_user()
    return redirect("login")

@app.route("/admin")
def admin() -> View:
    if current_user.username != 'admin':
        abort(404)

    students = db.session.query(Student).all()
    return render_template('admin.html', students=students)

@app.route("/admin/<student_id>")
def admin_student(student_id: str) -> View:
    if current_user.username != 'admin':
        abort(404)

    grades = get_insecure_db(student_id).read_grades()
    average = sum(grades.values()) / len(grades)
    student = db.session.query(Student).filter(Student.username==student_id).first()
    return render_template('admin_student.html', student=student, grades=grades, average=average)

@click.command()
@click.option("--debug", is_flag=True)
@click.option("--port", type=int, default=80)
@click.option("--grading-db", type=str, default="sqlite://")
@click.option("--root", type=str, default="/home")
def main(debug: bool, port: int, grading_db: str, root: str) -> None:
    app.config.update(
        SQLALCHEMY_DATABASE_URI=grading_db,
        student_root=root,
    )
    
    serve(port, debug, root)

if __name__ == "__main__":
    main()
