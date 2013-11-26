#!/bin/sh

INSTANCE=generic
DB=mozillians_org
cd /data/backups/bin/
rm -f anonymize.py
/usr/bin/wget -q -nH https://raw.github.com/mozilla/mozillians/master/scripts/mysql-anonymize/anonymize.py
/bin/chmod 755 anonymize.py

TODAY=`/bin/date +"%Y.%m.%d"`
HOSTNAME=`/bin/hostname`
SQLPATH=/data-2/$HOSTNAME/backups/$INSTANCE/sqlcopies/$DB
SQLFILE=$SQLPATH/$DB.$TODAY.sql
PASS=`/bin/grep ^password /data/$INSTANCE/$INSTANCE.cnf | /bin/cut -f2 -d= | /usr/bin/uniq`
if [ $PASS == ""]
then
P=""
else
P="-p$PASS"
fi

MYSQL="/usr/bin/mysql --defaults-file=/data/$INSTANCE/$INSTANCE.cnf -S /var/lib/mysql/$INSTANCE.sock"

# import db
$MYSQL -e "drop database if exists sanitize_$DB"
$MYSQL -e "create database if not exists sanitize_$DB"
$MYSQL sanitize_$DB < $SQLFILE

# sanitize db
/usr/bin/python anonymize.py anonymize_dev.yml > $SQLPATH/$DB.$TODAY.queries_sanitize.sql
$MYSQL sanitize_$DB < $SQLPATH/$DB.$TODAY.queries_sanitize.sql

# export db
/usr/bin/mysqldump -u root $P -S /var/lib/mysql/$INSTANCE.sock $DB > $SQLPATH/$DB.$TODAY.sanitized.sql
# copy db
