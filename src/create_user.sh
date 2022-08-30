#!/bin/bash

echo "Creating user: $1"
useradd "$1"
chgrp -R "lab1" "/home/$1" 
chmod g+rwx "/home/$1"
