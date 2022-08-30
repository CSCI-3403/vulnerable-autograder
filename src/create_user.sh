#!/bin/bash

echo "Creating user: $1"
useradd "$1"
touch "/home/$1/database.sqlite3"
chgrp -R "lab1" "/home/$1" 
chmod g+rwx "/home/$1"
