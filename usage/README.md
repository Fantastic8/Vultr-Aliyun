# Usage

Also see [中文文档](https://github.com/Fantastic8/Vultr-Aliyun/blob/master/usage/%E8%AF%BB%E6%88%91.md)

## Add Record

Select '1' to add a record and give your record a Label (The Label is just a name of your record, so name it whatever you want!).

![Add Record](https://raw.githubusercontent.com/Fantastic8/Vultr-Aliyun/master/images/AddRecord.png)

Program will list all of your Snapshots [Label, SNAPSHOTID, Date] on Vultr and ask you to choose one which you want to add into your record.

![Select Snapshot](https://raw.githubusercontent.com/Fantastic8/Vultr-Aliyun/master/images/AR_SelectSnapshot.png)

Then it will list all of your Server [Label, SUBID, Date] on Vultr and ask you to choose one which you want to add into your record.

![Select Server](https://raw.githubusercontent.com/Fantastic8/Vultr-Aliyun/master/images/AR_SelectServer.png)

Finally it will list all of your Domain records [Server, RecordID, IP] on Aliyun and ask you to choose one which you want to add into your record.

![Select Domain](https://raw.githubusercontent.com/Fantastic8/Vultr-Aliyun/master/images/AR_SelectDomainRecord.png)

When you see this message, it means that you have successfully added a new record to database, and you are ready to perform other operations.

![Add Success](https://raw.githubusercontent.com/Fantastic8/Vultr-Aliyun/master/images/AR_Success.png)

Other functions are similar usage.

## Menu

Option|Description
:--:|:--:
Add chain record| Add a new chain record, this record will connect vultr server, snapshot and domain record. WARNING: vultr server not exist in chain record will be deleted when monitoring.
Delete chain record| Delete a chain record. Delete a chain record will not delete vultr server or snapshot or domain record.
Show all servers| Show all servers information on **Vultr**
Show all snapshots| Show all snapshots information on **vultr**
Show Aliyun domain 'A' records| Show all 'A' domain record on **Aliyun**
Show server by label| Show all servers information on **vultr** by label 
Show snapshot by description| Show all snapshots information by description
Show Aliyun domain 'A' record by RRKeyWord| Show all 'A' domain record by key words
Show vultr account billing| Show your **vultr** billing
Repair chains immediately| Repair all chains immediately (including: check servers are available or not, and whether the domain records are correct)
Change ip immediately| Select a chain record, then change its IP by redeploying it. (place selectable)
Refresh| Refresh chain record
Start Monitoring| Start monitoring
