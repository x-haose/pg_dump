#!/bin/sh

export LANG=zh_CN.UTF-8

# 本地数据库配置，做导入的
DB_NAME=sale
DB_HOST="127.0.0.1"
DB_PORT=5432
DB_USER=postgres
DB_PASS=123456

# 远端数据库配置，做导出的
R_DB_NAME=
R_DB_HOST=
R_DB_USER=
R_DB_PORT=
R_DB_PASS=

usage() {
  echo "Usage:"
  echo "sh pg.sh -rh 192.168.100.64 -rp 5432 -ru odoo -rP Holder123 -rd sale -h 192.168.102.75 -p 5432 -u postgres -P 123456 -d sale"
  exit
}

while [ "$1" != "" ]; do
  case $1 in
  -d | --db)
    shift
    DB_NAME=$1
    ;;
  -h | --host)
    shift
    DB_HOST=$1
    ;;
  -p | --port)
    shift
    DB_PORT=$1
    ;;
  -u | --user)
    shift
    DB_USER=$1
    ;;
  -P | --passwd)
    shift
    DB_PASS=$1
    ;;
  -rd | --remote_db)
    shift
    R_DB_NAME=$1
    ;;
  -rh | --remote_host)
    shift
    R_DB_HOST=$1
    ;;
  -rp | --remote_port)
    shift
    R_DB_PORT=$1
    ;;
  -ru | --remote_user)
    shift
    R_DB_USER=$1
    ;;
  -rP | --remote_passwd)
    shift
    R_DB_PASS=$1
    ;;
  --help)
    usage
    ;;
  esac
  shift
done

command_exists() {
  command -v "$@" >/dev/null 2>&1
}

postgres_command() {
  cmd=$1
  passwd=$2
  /usr/bin/expect <<EOF
  set timeout 240
    spawn $cmd
    expect "*口令*"
    send "$passwd"
    send "\n"
    expect eof
EOF
}

load() {

  printf "开始导入数据库\n"

  create_db_cmd="createdb -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} ${DB_NAME}"
  printf "正在执行创建数据库命令：%s\n" "$create_db_cmd"
  postgres_command "$create_db_cmd" "${DB_PASS}"

  # 导入数据库
  restore_cmd="pg_restore -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -n public -Fc -j 6 -W ${DB_FILE}"
  printf "\n正在执行导入数据库命令：%s\n" "$restore_cmd"
  postgres_command "${restore_cmd}" "${DB_PASS}"

  # 清空表：ir_attachment
  clear_table_cmd="psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME} -c \"DELETE FROM ir_attachment;\""
  printf "\n正在执行清空表ir_attachment命令：%s\n" "$clear_table_cmd"
  postgres_command "${clear_table_cmd}" "${DB_PASS}"

  # 删除文件
  rm -rf "${DB_FILE}"

  printf "\n\n成功导入至目标数据库 %s 中！！！\n" "${DB_NAME}"
}

dump() {
  printf "开始导出数据库 \n"

  # 生成导出命令
  cmd="pg_dump -d ${R_DB_NAME} -h ${R_DB_HOST} -p ${R_DB_PORT} -U ${R_DB_USER} -v -W -Fc -n public --no-tablespaces -f ${DB_FILE}"
  printf "正在执行导出数据库命令：%s\n" "$cmd"

  postgres_command "${cmd}" "${R_DB_PASS}"

  size=$(wc -c <"$DB_FILE")
  if [ -f "${DB_FILE}" ] && [ "$size" -gt 0 ]; then
    printf "导出成功\n"
  else
    printf "导出失败\n"
    exit 2
  fi
}

main() {
  time=$(date "+%Y%m%d_%H%M%S")
  DB_FILE="${R_DB_NAME}_${time}.dump"

  dump
  load
}

main
# ./pg.sh -rh 192.168.100.64 -rp 5432 -ru odoo -rP Holder123 -rd sale -h 192.168.102.75 -p 5432 -u postgres -P 123456 -d sale
