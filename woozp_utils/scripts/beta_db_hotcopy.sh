#!/bin/bash
if [ -z "$2" ]; then
    echo "USAGE: $0 src_db mysql_root_password"
    exit 1
fi

SRC_DB=$1
MYSQL_ROOT_PWD=$2
BETA_DB=beta_${SRC_DB}
VAR_LIB_MYSQL=/var/lib/mysql

rm -rf ${VAR_LIB_MYSQL}/${BETA_DB}
mysqlhotcopy --user=root --password=${MYSQL_ROOT_PWD} "${SRC_DB}./~.*zipcodedistance/" "${BETA_DB}"
mysqladmin --user=root --password=${MYSQL_ROOT_PWD} refresh
cd ${VAR_LIB_MYSQL}/${BETA_DB}
if test -f ${VAR_LIB_MYSQL}/${SRC_DB}/*zipcodedistance.frm; then
    ln -s ${VAR_LIB_MYSQL}/${SRC_DB}/*zipcodedistance.MY* .
    cp ${VAR_LIB_MYSQL}/${SRC_DB}/*zipcodedistance.frm .
fi
