# ZJU_Auto
一些写（抄）的用于日常打卡的自动脚本

## 每周大学习.py

用于青春浙江公众号的大学习签到，灵感及原理来自[CC98此帖](https://www.cc98.org/topic/4991896/)。

使用需要抓包分析自己账号被分配给青春浙江的openId，直接修改即可运行。

ps：注意，需要之前有一次手动打卡，以便脚本获取历史信息，否则无法运行。

## 每日健康上报.py

哪个浙大学子不想拥有自己的蓝🐎呢？

基于[Tishacy](https://github.com/Tishacy/ZJU-nCov-Hitcarder)修改（抄），删掉了定时任务（因为我一般用Windows的任务计划程序）并添加了邮件反馈打卡结果。

使用时在main函数填入自己的账号密码，如果使用邮件反馈，需要自己配置相关的邮件服务器，用户密码收件人。