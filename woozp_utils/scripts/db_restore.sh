#!/bin/bash
if [ -z "$2" ]; then
    echo "USAGE: $0 src_folder dest_db"
    exit 1
fi

SRC_FOLDER="$1/$2"
DST_DB=$2
VAR_LIB_MYSQL=/var/lib/mysql

if test ! -d "${SRC_FOLDER}"; then
    echo "${SRC_FOLDER}" does not exist!
    exit 1
fi
cd "${VAR_LIB_MYSQL}/${DST_DB}"
cp "${SRC_FOLDER}"/* .
