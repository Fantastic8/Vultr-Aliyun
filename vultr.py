'''
@ Mark Zhang
created on 2018.3.6
'''

import ctypes
import inspect
import os
import sys
import json
import time
import pymysql
import datetime
import threading
import subprocess
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                        Config
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
MYSQL_USER=''
MYSQL_PASSWD=''
MYSQL_DB=''
VULTR_KEY = ''
ALI_ACCESS_KEY_ID = ''
ALI_ACCESS_KEY_SECRET = ''
client = AcsClient(ALI_ACCESS_KEY_ID , ALI_ACCESS_KEY_SECRET, 'cn-hangzhou')
DOMAIN_NAME=''
logf_name = 'vultr.log'
# interval must greater than 5 minutes
check_interval = 10
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                        Database
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# connect to database
con = pymysql.connect(
    host='localhost',
    port=3306,
    user=MYSQL_USER,
    passwd=MYSQL_PASSWD,
    db=MYSQL_DB,
)
cur = con.cursor()

cur.execute("create table if not exists Chains(" +
            "Label varchar(20) binary not null,"+
            "SNAPSHOTID varchar(20) binary UNIQUE not null," +
            "SUBID varchar(20) binary UNIQUE not null," +
            "RecordId varchar(20) binary UNIQUE not null,"+
            "Status varchar(10) binary not null," +
            "primary key(Label)" +
            ");")
con.commit()

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    tool
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# check ip: 0-success 1-fail
def ping(ip):
    p = subprocess.Popen([r'./ping.sh', ip], stdout=subprocess.PIPE)
    result = p.stdout.read()
    # print(result)
    if result == b'0\n' or result == b'0':
        # ----ping success----
        return True
    else:
        # ----ping fail----
        return False


def get_now():
    time = ''
    now = datetime.datetime.now()
    time += str(now.year) + '-'
    time += str(now.month) + '-'
    time += str(now.day) + ' '
    time += str(now.hour) + ':'
    time += str(now.minute) + ':'
    time += str(now.second)
    return time


def appendline_log(message):
    logf = open(logf_name, mode='a', encoding='utf-8')
    logf.writelines(get_now() + ' : ' + message+'\n')
    logf.flush()
    logf.close()


def appendline_error(message):
    logf = open(logf_name, mode='a', encoding='utf-8')
    logf.writelines(get_now() + ' ERROR: ' + message + '\n')
    logf.flush()
    logf.close()
    # !!!!Sent email!!!!!

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    Ali Cloud
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def get_domain_records(domain_name,TypeKeyWord=None,RRKeyWord=None):
    request = CommonRequest()
    request.set_domain('alidns.aliyuncs.com')
    request.set_version('2015-01-09')
    request.set_action_name('DescribeDomainRecords')
    request.add_query_param('DomainName', domain_name)
    if TypeKeyWord:
        request.add_query_param('TypeKeyWord', TypeKeyWord)
    if RRKeyWord:
        request.add_query_param('RRKeyWord', RRKeyWord)
    response = client.do_action_with_exception(request)
    results=json.loads(response.decode())
    return results


def get_domain_record_by_RecordId(RecordId):
    request = CommonRequest()
    request.set_domain('alidns.aliyuncs.com')
    request.set_version('2015-01-09')
    request.set_action_name('DescribeDomainRecordInfo')
    request.add_query_param('RecordId', RecordId)
    response = client.do_action_with_exception(request)
    results = json.loads(response.decode())
    return results


def change_record_ip(RecordId, ip):
    record=get_domain_record_by_RecordId(RecordId)
    request = CommonRequest()
    request.set_domain('alidns.aliyuncs.com')
    request.set_version('2015-01-09')
    request.set_action_name('UpdateDomainRecord')
    request.add_query_param('RecordId', RecordId)
    request.add_query_param('RR', record['RR'])
    request.add_query_param('Type', record['Type'])
    request.add_query_param('Value', ip)
    response = client.do_action_with_exception(request)
    results = json.loads(response.decode())
    if results['RecordId']==RecordId:
        appendline_log('Domain('+DOMAIN_NAME+') record('+RecordId+')\'s value changed to '+ip)
        print('Domain record change successfully!')
        return True
    else:
        appendline_error('Something went wrong when trying to change Domain(' + DOMAIN_NAME + ') record(' + RecordId + ')\'s value changed to ' + ip)
        print('Failed to change domain record!')
        return False


def change_record_ip_by_SUBID(RecordId,SUBID):
    return change_record_ip(RecordId,get_ip_by_SUBID(SUBID))
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    Vultr Account
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


def get_billing():
    results = os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/account/info').readlines()
    result = ''
    for line in results:
        result += line
    return json.loads(result)


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    Vultr region
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def get_regions():
    results = os.popen('curl https://api.vultr.com/v1/regions/list')
    result = ''
    for line in results:
        result += line
    return json.loads(result)


def get_VPSPLAN_by_DCID(DCID):
    results = os.popen('curl https://api.vultr.com/v1/regions/availability_vc2?DCID=' + str(DCID))
    result = ''
    if results==None:
        return None
    for line in results:
        result += line
    return json.loads(result)


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    Vultr Server
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

'''''''''
Status:
    active: when server is running normally
    stopped: when server is initializing
Power status:
    running: when server is running
Server state:
    ok: when server is running normally
    locked: when server is being snapshot
'''''''''


def get_servers():
    results = os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/server/list')
    result = ''
    for line in results:
        result += line
    return json.loads(result)


def get_server_by_label(label):
    servers = get_servers()
    for server in servers.keys():
        if servers[server].__contains__('label'):
            if servers[server]['label'] == label:
                return servers[server]
    return None


def get_SUBID_by_label(label):
    server = get_server_by_label(label)
    if server != None and isinstance(server, dict):
        if server.__contains__('SUBID'):
            return server['SUBID']
    return None


def get_server_by_SUBID(SUBID):
    servers = get_servers()
    for server in servers.keys():
        if servers[server].__contains__('SUBID'):
            if servers[server]['SUBID'] == SUBID:
                return servers[server]
    return None


def get_ip_by_SUBID(SUBID):
    server=get_server_by_SUBID(SUBID)
    if isinstance(server, dict) and server.__contains__('main_ip'):
        return server['main_ip']
    return None


def get_VPSPLANID_by_SUBID(SUBID):
    return get_server_by_SUBID(SUBID)['VPSPLANID']
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
Parameters:
DCID integer Location to create this virtual machine in.  See v1/regions/list
VPSPLANID integer Plan to use when creating this virtual machine.  See v1/plans/list
OSID integer Operating system to use.  See v1/os/list
ipxe_chain_url string (optional) If you've selected the 'custom' operating system, this can be set to chainload the specified URL on bootup, via iPXE
ISOID string (optional)  If you've selected the 'custom' operating system, this is the ID of a specific ISO to mount during the deployment
SCRIPTID integer (optional) If you've not selected a 'custom' operating system, this can be the SCRIPTID of a startup script to execute on boot.  See v1/startupscript/list
SNAPSHOTID string (optional) If you've selected the 'snapshot' operating system, this should be the SNAPSHOTID (see v1/snapshot/list) to restore for the initial installation.
enable_ipv6 string (optional) 'yes' or 'no'.  If yes, an IPv6 subnet will be assigned to the machine (where available)
enable_private_network string (optional) 'yes' or 'no'. If yes, private networking support will be added to the new server.
NETWORKID array (optional) List of private networks to attach to this server.  Use either this field or enable_private_network, not both
label string (optional) This is a text label that will be shown in the control panel
SSHKEYID string (optional) List of SSH keys to apply to this server on install (only valid for Linux/FreeBSD).  See v1/sshkey/list.  Separate keys with commas
auto_backups string (optional) 'yes' or 'no'.  If yes, automatic backups will be enabled for this server (these have an extra charge associated with them)
APPID integer (optional) If launching an application (OSID 186), this is the APPID to launch. See v1/app/list.
userdata string (optional) Base64 encoded user-data
notify_activate string (optional, default 'yes') 'yes' or 'no'. If yes, an activation email will be sent when the server is ready.
ddos_protection (optional, default 'no') 'yes' or 'no'.  If yes, DDOS protection will be enabled on the subscription (there is an additional charge for this)
reserved_ip_v4 string (optional) IP address of the floating IP to use as the main IP of this server
hostname string (optional) The hostname to assign to this server.
tag string (optional) The tag to assign to this server.
FIREWALLGROUPID string (optional) The firewall group to assign to this server. See /v1/firewall/group_list.
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


def create_server(DCID, VPSPLANID, OSID, label, SNAPSHOTID=None):
    if SNAPSHOTID != None and SNAPSHOTID != '':
        SNAPSHOTID = ' --data \'SNAPSHOTID=' + SNAPSHOTID + '\''
        OSID='164'
    results = os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/server/create --data \'DCID=' + DCID + '\' --data \'VPSPLANID=' + VPSPLANID + '\' --data \'OSID=' + OSID + '\'' + SNAPSHOTID + ' --data \'enable_ipv6=yes\' --data \'enable_private_network=yes\' --data \'label=' + label + '\' --data \'hostname=' + label + '\'')
    result = ''
    for line in results:
        result += line
    j=json.loads(result)
    try:
        appendline_log('A new Server('+j['SUBID']+') has been created')
    except:
        appendline_error('Something went wrong when trying to create a new Server with DCID='+str(DCID)+' VPSPLANID='+str(VPSPLANID)+' OSID='+str(OSID)+' label='+label+' SNAPSHOTID='+SNAPSHOTID)
    return j


def destroy_server(SUBID):
    os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/server/destroy --data \'SUBID=' + SUBID + '\'')
    appendline_log('A server with SUBID: '+SUBID+' has been destroyed.')


def reboot_server(SUBID):
    os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/server/reboot --data \'SUBID=' + SUBID + '\'')
    appendline_log('A server with SUBID: ' + SUBID + ' has been rebooted.')


def restore_snapshot_server(SUBID, SNAPSHOTID):
    os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/server/restore_snapshot --data \'SUBID=' + SUBID + '\' --data \'SNAPSHOTID=' + SNAPSHOTID + '\'')
    appendline_log('A server with SUBID: ' + SUBID + ' has been restored with snapshot whose SNAPSHOTID: '+SNAPSHOTID+'.')


def start_server(SUBID):
    os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/server/start --data \'SUBID=' + SUBID + '\'')
    appendline_log('A server with SUBID: ' + SUBID + ' has been started.')


def change_ip_by_Label(Label,DCID=None):
    cur.execute('select * from Chains where Label=\''+Label+'\'')
    chain=cur.fetchone()
    if not chain:
        appendline_error('Something went wrong when trying to change ip on chain with label - '+Label+' : Chain not exists')
        return
    server=get_server_by_SUBID(chain[2])
    if server != None and isinstance(server, dict) and server.__contains__('DCID') and server.__contains__('VPSPLANID') and server.__contains__('OSID') and server.__contains__('label'):
        SNAPSHOTID = chain[1]
        if SNAPSHOTID != None:
            # create new server
            if DCID==None:
                DCID=server['DCID']
            newserver = create_server(DCID, server['VPSPLANID'], server['OSID'], server['label'], SNAPSHOTID)
            try:
                cur.execute('update Chains set SUBID=\'' + newserver['SUBID'] + '\' where Label=\'' + Label + '\'')
                con.commit()
            except:
                con.rollback()
                appendline_error('Something went wrong when updating chain record('+Label+') with SUBID('+newserver['SUBID']+')')
                return

            # destroy old server
            destroy_server(server['SUBID'])

            #change aliyun domain record
            change_record_ip_by_SUBID(chain[3],newserver['SUBID'])
        else:
            appendline_error('Something went wrong when trying to get SNAPSHOTID from database using Label - ' + chain[0])
    else:
        appendline_error('Something went wrong when trying to analysis server json with SUBID - '+chain[2])


def change_ip():
    #select chain record
    cur.execute('select * from Chains')
    records = cur.fetchall()
    print('---------------- Chain Records ----------------')
    for index in range(len(records)):
        print(str(index + 1) + '. ' + records[index][0]+' '+records[index][4])
    try:
        Label = records[int(input('Please select a record you would like to change ip: ')) - 1][0]
    except:
        print('ERROR Input!\n')
        return

    #select DCID
    print('Regions available')
    regions=get_regions()
    regionslist=[]
    index=0
    for region in regions.keys():
        print(str(index+1)+'. '+regions[region]['name']+'  '+regions[region]['DCID'])
        regionslist.append(regions[region]['DCID'])
        index+=1
    selection=input('\nPlease select a region you would like to switch your server to(Default: same as old server): ')
    if selection==None or selection=='':
        change_ip_by_Label(Label)
    else:
        try:
            DCID = regionslist[int(selection)-1]
            cur.execute('Select * from Chains where Label=\''+Label+'\'')
            subid=cur.fetchone()[2]
            if int(get_VPSPLANID_by_SUBID(subid)) in get_VPSPLAN_by_DCID(DCID):
                change_ip_by_Label(Label,DCID)
            else:
                print('This region is currently not available')
                return
        except:
            print('Error Input!')
            return


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    Vultr Snapshot
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


def get_snapshots():
    results = os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/snapshot/list')
    result = ''
    for line in results:
        result += line
    return json.loads(result)


def get_snapshot_by_description(description):
    snapshots = get_snapshots()
    for snapshot in snapshots.keys():
        if snapshots[snapshot].__contains__('description'):
            if snapshots[snapshot]['description'] == description:
                return snapshots[snapshot]
    return None


def get_SNAPSHOTID_by_description(description):
    snapshot = get_snapshot_by_description(description)
    if snapshot != None and isinstance(snapshot, dict):
        if snapshot.__contains__('SNAPSHOTID'):
            return snapshot['SNAPSHOTID']
    return None


def create_snapshot(SUBID):
    results = os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/snapshot/create --data \'SUBID=' + SUBID + '\'')
    result = ''
    for line in results:
        result += line
    appendline_log('A new snapshot has been created by SUBID('+SUBID+')')
    return json.loads(result)


def destroy_snapshot(SNAPSHOTID):
    os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/snapshot/destroy --data \'SNAPSHOTID=' + SNAPSHOTID + '\'')
    appendline_log('A snapshot('+SNAPSHOTID+') has been destroyed')


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    Database
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def add_chain_record():
    Label=''
    SNAPSHOTID=''
    SUBID=''
    RecordId=''

    #Label
    Label=input('Input a Label to this new record: ')
    #check exists
    cur.execute('select * from Chains where Label=\''+Label+'\'')
    if cur.fetchone():
        print('This Label already exists!')
        return

    #select SNAPSHOTID
    print('--------Select Vultr SNAPSHOT--------')
    snapshots=get_snapshots()
    snapshotindex=[]
    ssindex=1
    for snapshot in snapshots.keys():
        print(str(ssindex)+'. '+snapshots[snapshot]['description']+'\t'+snapshots[snapshot]['SNAPSHOTID']+'\t'+snapshots[snapshot]['date_created'])
        snapshotindex.append(snapshots[snapshot]['SNAPSHOTID'])
        ssindex+=1
    try:
        SNAPSHOTID=snapshotindex[int(input('Please Select a Vultr Snapshot: '))-1]
    except:
        print('Error Input')
        return
    print('Selected Snapshot - '+SNAPSHOTID+'\n\n')

    #select SUBID
    print('--------Select Vultr Server--------')
    servers=get_servers()
    serverindex=[]
    sindex=1
    for server in servers.keys():
        print(str(sindex)+'. '+servers[server]['label']+' '+servers[server]['SUBID']+' '+servers[server]['date_created'])
        serverindex.append(servers[server]['SUBID'])
        sindex+=1
    try:
        SUBID=serverindex[int(input('Please Select a Vultr Server: '))-1]
    except:
        print('Error Input')
        return
    print('Selected Server - '+SUBID+'\n\n')

    #select RecordId
    print('--------Select Aliyun domain Record--------')
    records = get_domain_records(DOMAIN_NAME,'A')
    rindex = 0
    for rindex in range(len(records['DomainRecords']['Record'])):
        print(str(rindex+1) + '. ' + records['DomainRecords']['Record'][rindex]['RR'] + ' ' + records['DomainRecords']['Record'][rindex]['RecordId'] + ' ' + records['DomainRecords']['Record'][rindex]['Value'])
    try:
        RecordId=records['DomainRecords']['Record'][int(input('Please Select a domain record: ')) - 1]['RecordId']
    except:
        print('Error Input')
        return
    print('Selected Domain Record - ' + RecordId + '\n\n')

    #add chain record
    try:
        stat=check_status(SUBID,RecordId)
        cur.execute("insert into Chains values('"+Label+"','"+SNAPSHOTID+"','"+SUBID+"','"+RecordId+"','"+stat+"')")
        con.commit()
        print('New chain record added successfully!')
        appendline_log('A new chain record has been created. Label: '+Label+' SNAPSHOTID: '+SNAPSHOTID+' SUBID:'+SUBID+' RecordId: '+RecordId+' Status: '+stat)
    except:
        print('Cannot create this record. Notice: Label, SNAPSHOTID, SUBID and REcordID are UNIQUE in database.')
        con.rollback()


def delete_chain_record():
    cur.execute('select * from Chains')
    records=cur.fetchall()
    print('---------------- Chain Records ----------------')
    for index in range(len(records)):
        print(str(index+1)+'. '+records[index][0])
    try:
        Label=records[int(input('Please select a record you would like to delete: '))-1][0]
        cur.execute('delete from Chains where Label=\''+Label+'\'')
        con.commit()
        print('Delete chain record successfully!\n')
        appendline_log('A chain record has been deleted. Label: ' + Label )
    except:
        print('ERROR Input!\n')
        return

def check_status(SUBID,RecordId):
    if not ping('www.baidu.com'):
        return 'Unready'
    # ping ipv4
    ipv4 = get_server_by_SUBID(SUBID)['main_ip']
    if not ping(ipv4):
        return 'Blocked'
    else:  # check domain record value
        if ipv4 != get_domain_record_by_RecordId(RecordId)['Value']:
            return 'Mismatch'
    return 'Normal'

def check_chain_status_by_Label(Label):
    if not ping('www.baidu.com'):
        return 'Unready'
    cur.execute('select * from Chains where Label=\''+Label+'\'')
    chain=cur.fetchone()
    status=''
    if chain:
        server=get_server_by_SUBID(chain[2])
        if server==None:
            return 'Server Not Exists'
        if server['status'] != 'active' or server['power_status'] != 'running' or server['server_state'] != 'ok':
            return 'Unready'
        #ping ipv4
        ipv4=server['main_ip']
        if not ping(ipv4):
            return 'Blocked'
        else: #check domain record value
            if ipv4!=get_domain_record_by_RecordId(chain[3])['Value']:
                return 'Mismatch'
        return 'Normal'
        #ping domain
    else:
        return None

def check_chains():
    cur.execute('select * from Chains')
    chains=cur.fetchall()
    for chain in chains:
        try:
            cur.execute('update Chains set Status=\''+check_chain_status_by_Label(chain[0])+'\' where Label=\''+chain[0]+'\'')
            con.commit()
        except:
            con.rollback()
            print('Something went wrong when trying to update chain record - '+chain[0])
            appendline_error('Something went wrong when trying to update chain record - '+chain[0])


def repair_chain(Label):
    status=check_chain_status_by_Label(Label)
    cur.execute('select * from Chains where Label=\''+Label+'\'')
    chain =cur.fetchone()
    if status=='Blocked':
        print('A blocked chain(\''+Label+'\') has been detected! Repairing...')
        appendline_log('A blocked chain(\''+Label+'\') has been detected! Repairing...')
        change_ip_by_Label(Label)
    elif status=='Mismatch':
        print('A mismatch chain(\''+Label+'\') has been detected! Repairing...')
        appendline_log('A mismatch chain(\''+Label+'\') has been detected! Repairing...')
        change_record_ip_by_SUBID(chain[3],chain[2])
    #update status
    try:
        newstatus=check_chain_status_by_Label(Label)
        cur.execute('update Chains set Status=\'' + newstatus + '\' where Label=\'' + Label + '\'')
        con.commit()
        if status!='Blocked' and status!='Mismatch' and newstatus=='Normal':
            pass
        elif (status=='Blocked' or status=='Mismatch') and newstatus=='Normal':
            print('Chain(\''+Label+'\') has been repaired')
            appendline_log('Chain(\''+Label+'\') has been repaired')
        else:
            print('Failed to repaire chain(\''+Label+'\'), please check them manually!')
            appendline_log('Failed to repaire '+status+' chain(\''+Label+'\')')
    except:
        con.rollback()
        print('Something went wrong when trying to update chain record - ' + Label)
        appendline_error('Something went wrong when trying to update chain record - ' + Label)

def repair_chains():
    print('Checking chains...')
    cur.execute('select * from Chains')
    chains=cur.fetchall()
    #repair chains
    for chain in chains:
        repair_chain(chain[0])

    # clean up irrelevant servers
    servers = get_servers()
    find=False
    for server in servers.keys():
        find=False
        for chain in chains:
            if servers[server]['SUBID']==chain[2]:
                find=True
                break
        if not find:
            destroy_server(servers[server]['SUBID'])
    print('All chains have been checked')


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    threading
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
runflag=False


def monitoring():
    print('Start Monitor Chains')
    while True:
        for i in range(0,check_interval):
            for j in range(0,60):
                time.sleep(1)
        repair_chains()


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)
    print('Stop Monitoring Chains')

runthread=None
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    prints
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def print_server_information(server):
    if server == None or not isinstance(server, dict):
        print('Server not exists')
        return
    if server.__contains__('SUBID') and server.__contains__('main_ip'):
        print('----------------Server ' + str(server['SUBID']) + '----------------')
    else:
        return None
    if ping(str(server['main_ip'])):
        print('Life: Alive')
    else:
        print('Life: Dead')
    if server.__contains__('label'):
        print('Label: ' + server['label'])
    if server.__contains__('power_status'):
        print('Power status: ' + server['power_status'])
    if server.__contains__('date_created'):
        print('Date created: ' + server['date_created'])
    if server.__contains__('os'):
        print('Operation System: ' + server['os'])
    print('IP: ' + str(server['main_ip']))
    if server.__contains__('location'):
        print('Location: ' + server['location'])
    if server.__contains__('status'):
        print('Status: ' + server['status'])
    if server.__contains__('server_state'):
        print('Server state: ' + server['server_state'])
    if server.__contains__('ram'):
        print('Ram: ' + server['ram'])
    if server.__contains__('disk'):
        print('Disk: ' + server['disk'])
    if server.__contains__('DCID'):
        print('DCID: ' + str(server['DCID']))
    if server.__contains__('OSID'):
        print('OSID: ' + str(server['OSID']))
    if server.__contains__('VPSPLANID'):
        print('VPSPLANID: ' + str(server['VPSPLANID']))
    if server.__contains__('cost_per_month'):
        print('Cost per month: ' + str(server['cost_per_month']))
    if server.__contains__('current_bandwidth_gb'):
        print('Current bandwidth/G: ' + str(server['current_bandwidth_gb']))
    if server.__contains__('allowed_bandwidth_gb'):
        print('Allowed bandwidth/G: ' + str(server['allowed_bandwidth_gb']))
    print('')


def print_servers_information():
    servers = get_servers()
    for server in servers.keys():
        print_server_information(servers[server])
        print('')
    print('\n')


def print_snapshot_information(snapshot):
    if snapshot == None or not isinstance(snapshot, dict):
        print('Snapshot not exists')
        return
    if snapshot.__contains__('SNAPSHOTID'):
        print('----------------Snapshot ' + str(snapshot['SNAPSHOTID']) + '----------------')
    if snapshot.__contains__('date_created'):
        print('Date created: ' + snapshot['date_created'])
    if snapshot.__contains__('description'):
        print('Description: ' + snapshot['description'])
    if snapshot.__contains__('size'):
        print('Size: ' + str(snapshot['size']))
    if snapshot.__contains__('status'):
        print('Status: ' + snapshot['status'])
    print('')


def print_snapshots_information():
    snapshots = get_snapshots()
    for snapshot in snapshots.keys():
        print_snapshot_information(snapshots[snapshot])
        print('')
    print('\n')


def print_billing():
    billing = get_billing()
    print('----------------Billing----------------')
    if billing.__contains__('balance'):
        print('Balance: ' + billing['balance'])
    if billing.__contains__('pending_charges'):
        print('Pending charges: ' + billing['pending_charges'])
    if billing.__contains__('last_payment_date'):
        print('Last payment date: ' + billing['last_payment_date'])
    if billing.__contains__('last_payment_amount'):
        print('Last payment amount: ' + billing['last_payment_amount'])
    print('')


def print_domain_record(record):
    print('****RecordId '+record['RecordId']+'****')
    print('RR: ' + record['RR'])
    print('Type: ' + record['Type'])
    print('Value: ' + record['Value'])
    print('Line: ' + record['Line'])
    print('TTL: ' + str(record['TTL']))
    print('Status: ' + record['Status'])


def print_domain_records(TypeKeyWord=None,RRKeyword=None):
    results=get_domain_records(DOMAIN_NAME,TypeKeyWord,RRKeyword)
    print('----------------'+DOMAIN_NAME+'----------------')
    print('Total count: '+str(results['TotalCount'])+'\n')
    for record in results['DomainRecords']['Record']:
        print_domain_record(record)
        print('')
    print('\n')


def show_chains():
    cur.execute('select * from Chains')
    chains=cur.fetchall()
    print('+------------------------+------------------------+------------------------+-------------------------+----------+')
    print('|          Label         |       SNAPSHOTID       |        SUBID           |        RecordID         |  Status  |')
    print('+------------------------+------------------------+------------------------+-------------------------+----------+')
    for chain in chains:
        print('|%-24s'%chain[0]+'|%-24s'%chain[1] +'|%-24s'%chain[2]+'|%-25s'%chain[3]+'|%-10s'%chain[4]+'|')
    print('+------------------------+------------------------+------------------------+-------------------------+----------+')

def show_menu():
    print('==================Auto Vultr & Aliyun ==================')
    if not runflag:
        print('1. Add chain record')
        print('2. Delete chain record')
        print('3. Show all servers')
        print('4. Show all snapshots')
        print('5. Show Aliyun domain \'A\' records')
        print('6. Show server by label')
        print('7. Show snapshot by description')
        print('8. Show Aliyun domain \'A\' record by RRKeyWord')
        print('9. Show vultr account billing')
        print('10. Repair chains immediately')
        print('11. Change ip immediately')
        print('12. Refresh')
        print('13. Start Monitoring')
    else:
        print('1. Stop Monitoring')
    print('Enter \'quit\' to quit program')


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    main
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
show_chains()
show_menu()
command = input('Please select: ')
while command != 'quit':
    os.system('clear')
    show_chains()
    if not runflag:
        if command == '1': #Add chain record
            add_chain_record()
        elif command == '2':  #Delete chain record
            delete_chain_record()
        elif command == '3':  # show all servers
            print_servers_information()
        elif command == '4':  # show all snapshots
            print_snapshots_information()
        elif command == '5':  # show aliyun domain 'A' records
            print_domain_records('A')
        elif command == '6':  # show server by label
            print_server_information(get_server_by_label(input('\nPlease Enter the label of server: ')))
        elif command == '7':  # show snapshot by description
            print_snapshot_information(get_snapshot_by_description(input('\nPlease Enter the description of snapshot: ')))
        elif command == '8':  # show aliyun domain 'A' record by RRKeyword
            print_domain_records('A',input('\nPlease Enter the RRKeyword of domain record: '))
        elif command == '9':  # show account billing
            print_billing()
        elif command == '10':  # repair chains immediately
            repair_chains()
        elif command == '11':  # change ip immediately
            change_ip()
        elif command == '12': #refresh
            check_chains()
            os.system('clear')
            show_chains()
        elif command == '13': # start
            runthread = threading.Thread(target=monitoring)
            runthread.start()
            runflag = not runflag
        else:
            print('Error selection!\n')
    else:
        if command == '1':
            stop_thread(runthread)
            runflag = not runflag
        else:
            print('Error selection!\n')
    show_menu()
    command = input('Please select: ')
if runthread!=None and runflag==True:
    stop_thread(runthread)
con.close()
print('==========================Auto Vultr has been terminated==========================')

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                        Vultr_server Database Design
create table if not exists Chains(
    Label varchar(20) binary not null,
    SNAPSHOTID varchar(20) binary UNIQUE not null,
    SUBID varchar(20) binary UNIQUE not null,
    RecordId varchar(20) binary UNIQUE not null,
    Status varchar(10) binary not null,
    primary key(Label)
);

''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                        How it works
This program will automatically ping all the server you have, and whenever it detects a server out of reach, it will destroy 
the server on your vultr account and create a new server with same plan and same snapshot. And it will change the domain 
analysis to specific server on aliyun.
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
