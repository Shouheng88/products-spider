#!/bin/bash
nohup python /home/box_admin_wsh/shuma/python/run.py -c crawl_jd_goods -e server_local > goods.out 2>&1 &
