#!/bin/bash
if [ -z "$3" ]; then
    echo "USAGE: $0 src_db dest_folder mysql_root_password"
    exit 1
fi

SRC_DB=$1
DST_FOLDER=$2
MYSQL_ROOT_PWD=$3
VAR_LIB_MYSQL=/var/lib/mysql

if test -e "${DST_FOLDER}"; then
    echo "${DST_FOLDER}" should not exist
    exit 1
fi
mkdir -p "${DST_FOLDER}"
mysqlhotcopy --user=root --password=${MYSQL_ROOT_PWD} "${SRC_DB}./~.*zipcodedistance/" "${DST_FOLDER}"
cd "${DST_FOLDER}"
