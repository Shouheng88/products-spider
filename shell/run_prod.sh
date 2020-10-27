#!/bin/bash
# Author: WangShouheng
# Email: shouheng2015@gmail.com
# The shell script for shuma spider
root_dir=/home/box_admin_wsh  # 指定程序的根目录
environment=server_local      # 指定程序适用的服务器环境
# 用法
usage () {
  echo "使用说明:"
  echo "基础命令：sh 脚本名称.sh [start|stop|restart|status] [command] [params]"
  echo "参数说明："
  echo ""
  echo "start   : 启动程序"
  echo "stop    : 停止程序"
  echo "restart : 重启程序"
  echo "status  : 程序状态"
  echo ""
  echo "command : 程序运行的命令，直接传递给 run.py 作为 -c 参数，取值及含义"
  echo "          write_category     : 写入品类处理结果"
  echo "          crawl_jd_category  : 爬取京东品类信息"
  echo "          crawl_jd_goods     : 爬取京东商品列表"
  echo "          crawl_jd_detail    : 爬取京东商品详情"
  echo "          crawl_jd_discount  : 爬取京东折扣信息"
  echo "          crawl_jd_prices    : 爬取京东价格数据"
  echo "          crawl_hisotry      : 爬取历史价格信息"
  echo "params  : 个别 python 命令的附加参数"
}
# 开始
start() {
  is_exist $1
  # 不允许多次重复运行
  if [ $? -eq "0" ]; then
    echo "$1 is running with pid ${pid}"
  else
    if [ ! $2 ]; then
      nohup python $root_dir/shuma/python/run.py -c $1 -e $environment > console.out 2>&1 & 
    else
      nohup python $root_dir/shuma/python/run.py -c $1 -e $environment -a $2 > console.out 2>&1 & 
    fi
  fi
}
# 结束
stop () {
  is_exist $1
  if [ $? -eq "0" ]; then
    kill -9 $pid
	echo "$1 was killed with pid ${pid}"
  else
    echo "$1 is NOT running" 
  fi
}
# 重新开始
restart () {
  stop $1 $2
  start $1 $2
}
# 状态
status () {
  is_exist $1
  if [ $? -eq "0" ]; then
    echo "$1 is running with pid ${pid}"
  else
    echo "$1 is NOT running" 
  fi
}
# 判断指定的指令是否存在进程
is_exist() {
  # 获取指定的 command 的 pid，由于执行 shell 时的命令也包含了 $1 所以，需要过滤 /bin/bash
  pid=`ps -ef | grep $1 | grep -v grep | grep -v '/bin/bash' | awk '{print $2}'`
  # -z 表示字符串为空时为真
  if [ -z "${pid}" ]; then
    return 1
  else
    return 0
  fi
}
# 对指令进行判断
case "$1" in
"start")
start $2 $3
;;
"stop")
stop $2 $3
;;
"status")
status $2 $3
;;
"restart")
restart $2 $3
;;
*)
usage
;;
esac

# Ending the shell ...
