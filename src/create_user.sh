#!/bin/bash

echo "Creating user: $1"
useradd "$1"

sqlite3 "/home/$1/database.sqlite3" << EOF
DROP TABLE IF EXISTS grades;
CREATE TABLE grades (student TEXT, assignment INT, score INT);
INSERT INTO grades VALUES
    ('$1', 1, 0),
    ('$1', 2, 0),
    ('$1', 3, 0),
    ('$1', 4, 0),
    ('Alice', 1, 100),
    ('Alice', 2, 90),
    ('Alice', 3, 100),
    ('Alice', 4, 100),
    ('Bob', 1, 80),
    ('Bob', 2, 70),
    ('Bob', 3, 100),
    ('Bob', 4, 80);
EOF

sudo usermod -a -G "students" "$1"
chgrp "$1" "/home/$1/database.sqlite3" 
chown "$1" "/home/$1/database.sqlite3" 
chmod g+rwx "/home/$1"
