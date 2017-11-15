#!/bin/sh

# environment variables aren't forwarded to cron,
# so dump them and source .profile from crontab.

env | sed 's/^\(.*\)$/export \1/g' > /root/.profile
cron -f
