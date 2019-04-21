# Vultr-Aliyun

**Vultr-Aliyun** is a command-line tool which helps to automatically redeploy blocked server and synchronize with [**Aliyun**](https://wanwang.aliyun.com/domain/com/?spm=5176.10695662.1158081.1.4fde4234L5A46c) domain and [**Vultr**](https://www.vultr.com/) snapshot.

Also see [中文文档](https://github.com/Fantastic8/Vultr-Aliyun/blob/master/%E8%AF%BB%E6%88%91.md)

## Quick Start
To run **Vultr-Aliyun** tool:

```
python3 vultr.py
``` 

And you can see a list of all your records and main menu.

![Main Menu](https://raw.githubusercontent.com/Fantastic8/Vultr-Aliyun/master/images/main.png)

Then select ```13``` to start monitoring.

![Monitoring](https://raw.githubusercontent.com/Fantastic8/Vultr-Aliyun/master/images/monitoring.png)

It's better if you run this tool as a background process, so that monitoring process will continue when you log out from SSH, and you can achieve that by using [**screen**](https://linux.die.net/man/1/screen).


## Prerequisites
+ An inland linux server (Master)
+ Vultr Servers (Slave)
+ Aliyun Domain
+ [**Aliyun API**](https://helpcdn.aliyun.com/document_detail/53045.html?parentId=30347)
+ [**Vultr API**](https://www.vultr.com/api/)

## Requirements
+ python3
+ mysql
+ pymysql
+ [Aliyun SDK](https://help.aliyun.com/document_detail/53090.html) 
+ [tcping](https://gist.github.com/cnDelbert/5fb06ccf10c19dbce3a7)

## Installation

Install Mysql

Install [tcping](https://gist.github.com/cnDelbert/5fb06ccf10c19dbce3a7)

Install python3:

```
sudo apt-get install python3
```

Install pymysql

Install Aliyun SDK:

```
sudo pip3 install aliyun-python-sdk-core-v3
```

Download **Vultr-Aliyun** using git clone:

```
git clone https://github.com/Fantastic8/Vultr-Aliyun.git
```

## Configuration

Set up **Mysql**:

1. Create a mysql user
2. Create a database for **Vultr-Aliyun**

Set up **vultr.py**:

```
cd Vultr-Aliyun
vi vultr.py
```

Modify the following:

```
MYSQL_USER = 'Your mysql user name'
MYSQL_PASSWD = 'Your mysql user password'
MYSQL_DB = 'Your mysql database name'
VULTR_KEY = 'Vultr api key'
ALI_ACCESS_KEY_ID = 'Aliyun access key id'
ALI_ACCESS_KEY_SECRET = 'Aliyun access key secret'
client = AcsClient(ALI_ACCESS_KEY_ID, ALI_ACCESS_KEY_SECRET, 'cn-hangzhou')
DOMAIN_NAME = 'Aliyun domain name'
logf_name = 'vultr.log' # vultr log file name

# interval better be greater than 5 minutes
CHECK_INTERVAL_MAX = 10 # maximum check interval (minutes)
CHECK_INTERVAL_MIN = 4  # minimum check interval (minutes)
check_int = CHECK_INTERVAL_MAX
CHECK_PORT = '1010' # slave's port which master will use tcping to check, make sure this port is open on slave server!
```

After that, you can run **vultr.py**:

```
python3 vultr.py
```

### Why you need a Vultr Snapshot

When you deploy a server on **vultr**, there is a chance that this **IP** will be blocked in the future. So after configuration of your server and keeping all services running, you can create a **snapshot** of server so that it will automatically resume to the point where you create a snapshot at when this server has been blocked.

## Structure

![Structure](https://raw.githubusercontent.com/Fantastic8/Vultr-Aliyun/master/images/structure.png)

## Usage

See [**usage**](https://github.com/Fantastic8/Vultr-Aliyun/blob/master/usage/README.md) for more details.

## Warning
+ All vultr servers that not exist in chain record will be **deleted** !!!!!! Please add all your vultr servers into chain record.
+ Please prepare your vultr servers, snapshots and Aliyun domain records first, then add chain record in **Vultr-Aliyun**.
+ Please **delete** related **chain record** before you delete server instance or snapshot or domain record.
+ Please check **vultr.log** if anything goes wrong.
+ Usually need to wait until second checking interval to repair chain completely, because server needs time to reboot.


# Author

+ [**Pink Beast**](https://github.com/Fantastic8)

