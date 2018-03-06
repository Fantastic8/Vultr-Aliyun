# Vultr-Aliyun
定时检测vultr服务器连接情况并自动修复的python3程序

# 项目简介
此程序用于定时检测vultr服务器ip是否故障。若故障则将自动删除并重新创建新的服务器然后自动连接到对应的域名下。


# 平台
	1. 阿里云，并需要有可使用域名
	2. Vultr
	3. 一台国内服务器


# 服务器运行环境
	1. Linxu操作系统
	2. Python3
	3. Mysql
	4. 阿里云核心SDK包 (运行命令行: Sudo pip3 install aliyun-python-sdk-core-v3 安装)

# 运行之前
将vultr.py中config部分的变量修改：
	MYSQL_USER='mysql用户名'
	MYSQL_PASSWD='mysql密码'
	MYSQL_DB='mysql数据库名'
	VULTR_KEY='Vultr账户API Key，需要在Vultr账户中启用。请谨慎保管！'
	ALI_ACCESS_KEY_ID='阿里云用户Access Key ID，需要在阿里云账户中申请。请谨慎保管！'
	ALI_ACCESS_KEY_SECRET='与Access Key ID对应的Access Key Secret，请谨慎保管！'
	DOMAIN_NAME='阿里云的域名(eg: mydomain.com)'
	check_interval=检查时间间隔(至少要大于5)
	


# 运行方法
	1. 从Github上下载源码
	2. cd vultr
	3. python3 vultr.py


# 菜单说明
1.Add chain record - 添加一条链记录，链记录将Vultr服务器与Snapshot与域名解析连接起来。注意！所有没有被添加进链记录的Vultr主机会在定时检测时被自动  删除！！！为了防止Server在创建五分钟之内不能被删除的情况。
2.Delete chain record - 删除一条链记录。删除链记录不会直接删除服务器或是snapshot或是域名解析。
3.Show all servers - 显示Vultr账户上所有主机信息
4.Show all snapshots - 显示Vultr账户上所有Snapshot信息
5.Show Aliyun domain 'A' records - 显示阿里云账户上所有A记录的域名解析
6.Show server by label - 通过标签查找Vultr账户上的主机，并显示该主机信息
7.Show snapshot by description - 通过描述查找Vultr账户上的Snapshot，并显示该Snapshot信息
8.Show Aliyun domain 'A' record by RRKeyWord - 通过主机名模糊查找阿里云账户上的A记录的域名解析
9.Show vultr account billing - 显示Vultr账户账单
10.Repair chains immediately - 立刻修复所有链记录(修复包括：检查服务器是否能ping通，检查域名解析是否正确。程序会自动修复链记录的错误)
11.Change ip immediately - 选择一条链记录，修改它的ip地址(修改ip地址可以选择服务器地区。并会删除旧服务器创建新服务器)
12.Refresh - 刷新链记录状态
13.Start Monitoring - 开始监控(监控时无法查看以上所有内容，只有在退出监控后才能使用上述所有功能)

# 注意事项
	1. 请先在Vultr中创建好你的服务器，Snapshot和在阿里云上添加新的主机域名解析。之后再在程序中添加chain record然后选择13 开始自动检测。
删除Server或者Snapshot或者Domain record之前请先将包含其中之一的chain record删除，否则程序会报错。（没有写这一块的错误处理）
