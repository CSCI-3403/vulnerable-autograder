for user in $(cat secrets/valid_users.txt); do ./create_user.sh $user; done
