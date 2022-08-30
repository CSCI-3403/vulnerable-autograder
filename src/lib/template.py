import os
import sqlite3
import sys

{student_code}

test_cases = [
    ([1, 2, 3], 3),
    ([3, 1, 2], 3),
    ([1, 1, 1], 1),
    ([-1, -2, -3], -1),
]

def run_sql(sql: str):
    connection = sqlite3.connect("database.sqlite3")
    cur = connection.cursor()
    cur.execute(sql)
    connection.commit()

def update_grade(percent: float, assignment: int):
    run_sql("UPDATE grades SET score = " + str(percent) + " WHERE student='{student}' AND assignment=" + str(assignment))

def main():
    num_correct = 0

    for input, expected_output in test_cases:
        student_output = find_max(input)
        if student_output == expected_output:
            print("[*] Test passed for input {{}}".format(input))
            num_correct += 1
        else:
            print("[!] Test failed for input {{}}: Expected {{}}, got {{}}".format(
                input,
                expected_output,
                student_output))
    
    percent = num_correct / len(test_cases) * 100
    update_grade(percent, {assignment})

    if num_correct == len(test_cases):
        print("All tests passed")
    else:
        print("{{}}/{{}} tests passed".format(num_correct, len(test_cases)))
        exit(1)

main()