'''
@ Pink Beast
created on 2018.3.6
'''
import ctypes
import inspect
import os
import json
import time
import pymysql
import datetime
import traceback
import threading
import subprocess
from random import choice
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                        Config
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
MYSQL_USER = '' # mysql database user name
MYSQL_PASSWD = '' # mysql database user password
MYSQL_DB = '' # mysql database name
VULTR_KEY = '' # vultr api key
ALI_ACCESS_KEY_ID = '' # Aliyun access key id
ALI_ACCESS_KEY_SECRET = '' # Aliyun access key secret
client = AcsClient(ALI_ACCESS_KEY_ID, ALI_ACCESS_KEY_SECRET, 'cn-hangzhou')
DOMAIN_NAME = '' # Aliyun domain name
logf_name = 'vultr.log' # vultr log file name
# interval better be greater than 5 minutes
CHECK_INTERVAL_MAX = 10 # maximum check interval (minutes)
CHECK_INTERVAL_MIN = 4 # # minimum check interval (minutes)
check_int = CHECK_INTERVAL_MAX
CHECK_PORT = '1010' # slave's port which master will use tcpping to check, make sure this port is open on slave server!
RANDOM_REGION = True # True: randomly select new region from REGION_LIST when detected a blocked server; False: keep the same region as the old server
REGION_LIST = ['Atlanta', 'Dallas', 'Chicago', 'Los Angeles', 'Silicon Valley', 'Seattle', 'Miami'] # regions that can be randomly selected for new server
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
            "RecordId varchar(20) binary UNIQUE not null," +
            "Status varchar(10) binary not null," +
            "primary key(Label)" +
            ");")
con.commit()

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    tool
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
# check ip: 0-fail 1-success
def ping(ip):
    p = subprocess.Popen([r'./ping.sh', ip], stdout=subprocess.PIPE)
    result = p.stdout.read()
    # print(result)
    if result == b'1\n' or result == b'1':
        # ----ping success----
        return True
    else:
        # ----ping fail----
        return False

# check ip: 0-fail 1-success
def tcpping(ip, port, hierarchy=3):
    p = subprocess.Popen([r'./tcpping.sh', ip, port], stdout=subprocess.PIPE)
    result = p.stdout.read()
    # print(result)
    if result == b'5\n' or result == b'5':
        # ----ping success----
        return True
    elif result == b'0\n' or result == b'0':
        # ----ping fail----
        return False
    else:
        print(result)
        appendline_error('tcpping(\'' + str(ip) + '\', \'' + str(port) + '\') ' + str(result), 'TCPPING', hierarchy)


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


def appendline_log(message, label, hierarchy=0):
    try:
        logf = open(logf_name, mode='a', encoding='utf-8')

        formatl = ''
        for i in range(0, hierarchy):
            formatl += '\t'

        logf.writelines('%-20s' % get_now() + ': ' + label + '\n')
        for line in message.split('\n'):
            logf.writelines('                     ' + formatl + line + '\n')

        logf.flush()
        logf.close()
    except:
        traceback.print_exc()


def appendline_error(message, label, hierarchy=0):
    try:
        logf = open(logf_name, mode='a', encoding='utf-8')

        formatl = ''
        for i in range(0, hierarchy):
            formatl += '\t'

        logf.writelines('%-20s' % get_now() + ': \033[1;31;40m\tERROR\033[0m in ' + label + '\n')
        message += '\n'+traceback.format_exc()
        for line in message.split('\n'):
            logf.writelines('                     ' + formatl + line + '\n')
        logf.flush()
        logf.close()
    except:
        traceback.print_exc()

'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    Ali Cloud
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


def get_domain_records(domain_name, TypeKeyWord = None, RRKeyWord = None, hierarchy=2):
    request = CommonRequest()
    request.set_domain('alidns.aliyuncs.com')
    request.set_version('2015-01-09')
    request.set_action_name('DescribeDomainRecords')
    request.add_query_param('DomainName', domain_name)
    if TypeKeyWord:
        request.add_query_param('TypeKeyWord', TypeKeyWord)
    if RRKeyWord:
        request.add_query_param('RRKeyWord', RRKeyWord)
    try:
        response = client.do_action_with_exception(request)
        results=json.loads(response.decode())
        return results
    except:
        print('Something went wrong when trying to get domain records')
        appendline_error('get_domain_records(\''+str(domain_name)+'\',\''+str(TypeKeyWord)+'\',\''+str(RRKeyWord)+'\')', 'GET DOMAIN RECORD', hierarchy)
        return None


def get_domain_record_by_RecordId(RecordId, hierarchy=2):
    request = CommonRequest()
    request.set_domain('alidns.aliyuncs.com')
    request.set_version('2015-01-09')
    request.set_action_name('DescribeDomainRecordInfo')
    request.add_query_param('RecordId', RecordId)
    try:
        response = client.do_action_with_exception(request)
        results = json.loads(response.decode())
        return results
    except:
        print('Something went wrong when trying to get domain record by recordid from \'get_domain_record_by_RecordId(\''+RecordId+'\')')
        appendline_error('get_domain_record_by_RecordId(\'' + str(RecordId) + '\')', 'GET DOMAIN RECORD BY RECORDID', hierarchy)
        return None

def change_record_ip(RecordId, ip, hierarchy=2):
    record=get_domain_record_by_RecordId(RecordId)
    if record==None or not isinstance(record,dict) or not record.__contains__('RR') or not record.__contains__('Type') or ip==None:
        print('Something went wrong when tyring update domain record(record=\''+str(record)+'\') from \'change_record_ip(\'' + RecordId + '\',\'' + ip + '\')\'')
        appendline_error('change_record_ip(\'' + str(RecordId) + '\',\'' + str(ip) + '\') - record = \'' + str(record) + '\')', 'CHANGE RECORD IP', hierarchy)
        return None
    request = CommonRequest()
    request.set_domain('alidns.aliyuncs.com')
    request.set_version('2015-01-09')
    request.set_action_name('UpdateDomainRecord')
    request.add_query_param('RecordId', RecordId)
    request.add_query_param('RR', record['RR'])
    request.add_query_param('Type', record['Type'])
    request.add_query_param('Value', ip)
    try:
        response = client.do_action_with_exception(request)
        results = json.loads(response.decode())
    except:
        print('Something went wrong when tyring update domain record(\''+record['RR']+'.'+DOMAIN_NAME+'\') from \'change_record_ip(\''+RecordId+'\',\''+ip+'\')\'')
        appendline_error('change_record_ip(\'' + str(RecordId) + '\',\'' + str(ip) + '\') - record(\'' + str(record['RR']) + '.' + str(DOMAIN_NAME) + '\')', 'CHANGE RECORD IP', hierarchy)
        return False
    if results['RecordId'] == RecordId:
        appendline_log('Domain(\''+str(record['RR'])+'.'+str(DOMAIN_NAME)+'\') record('+str(RecordId)+')\'s value changed to '+str(ip), 'CHANGE RECORD IP', hierarchy)
        print('Domain record change successfully!')
        return True
    else:
        appendline_error('change_record_ip(\'' + str(RecordId) + '\',\'' + str(ip) + '\') - record(\'' + str(record['RR']) + '.' + str(DOMAIN_NAME) + '\')', 'CHANGE RECORD IP', hierarchy)
        print('Failed to change domain record!')
        return False


def change_record_ip_by_SUBID(RecordId,SUBID):
    return change_record_ip(RecordId, get_ip_by_SUBID(SUBID))
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    Vultr Account
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''


def get_billing(hierarchy=1):
    results = os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/account/info').readlines()
    result = ''
    for line in results:
        result += line
    try:
        j = json.loads(result)
        return j
    except:
        appendline_error('get_billing() - result = ' + str(result), 'GET BILLING', hierarchy)
        return None



'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    Vultr region
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def get_regions(hierarchy=1):
    results = os.popen('curl https://api.vultr.com/v1/regions/list')
    result = ''
    for line in results:
        result += line
    try:
        j=json.loads(result)
        return j
    except:
        appendline_error('get_regions() - result = ' + str(result), 'GET REGIONS', hierarchy)
        return None


def get_VPSPLAN_by_DCID(DCID, hierarchy=1):
    results = os.popen('curl https://api.vultr.com/v1/regions/availability_vc2?DCID=' + str(DCID))
    result = ''
    if results==None:
        return None
    for line in results:
        result += line
    try:
        j=json.loads(result)
        return j
    except:
        appendline_error('get_VPSPLAN_by_DCID(' + str(DCID) + ') - result = ' + str(result), 'GET VPS PLAN BY DCID', hierarchy)
        return None


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


def get_servers(hierarchy=1):
    results = os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/server/list')
    result = ''
    for line in results:
        result += line
    try:
        #print(result)
        j = json.loads(result)
        return j
    except:
        print('Something went wrong when trying to get json object from \'get_servers()\' function')
        appendline_error('get_servers() - result = ' + str(result), 'GET SERVERS', hierarchy)
        return None



def get_server_by_label(label):
    servers = get_servers()
    if servers==None or not isinstance(servers,dict):
        return None
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
    if servers==None or not isinstance(servers,dict):
        return None
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
    createquery='curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/server/create --data \'DCID=' + str(DCID) + '\' --data \'VPSPLANID=' + str(VPSPLANID) + '\' --data \'OSID=' + str(OSID) + '\'' + str(SNAPSHOTID) + ' --data \'enable_ipv6=yes\' --data \'enable_private_network=yes\' --data \'label=' + label + '\' --data \'hostname=' + label + '\''
    results = os.popen(createquery)
    result = ''
    for line in results:
        result += line
    try:
        j = json.loads(result)
        appendline_log('Created new Server( '+str(label)+' ) with SUBID '+j['SUBID'], 'CREATE SERVER', 2)
        return j
    except:
        appendline_error('create_server(\''+str(DCID)+'\', \''+str(VPSPLANID)+'\',\'' + str(OSID)+'\',\'' + str(label)+'\', \'' + str(SNAPSHOTID) + '\')', 'CREATE SERVER', 2)
        return None



def destroy_server(SUBID, label=None):
    os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/server/destroy --data \'SUBID=' + SUBID + '\'')
    appendline_log('Destroyed server( '+('Irrelevant' if label==None else str(label))+' ) with SUBID : '+str(SUBID)+' .', 'DESTROY SERVER', 2)


def reboot_server(SUBID, label=None):
    os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/server/reboot --data \'SUBID=' + SUBID + '\'')
    appendline_log('Rebooted server( '+str(label)+' ) with SUBID : ' + str(SUBID) + ' .', 'REBOOT SERVER', 2)


def restore_snapshot_server(SUBID, SNAPSHOTID,label=None):
    os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/server/restore_snapshot --data \'SUBID=' + SUBID + '\' --data \'SNAPSHOTID=' + SNAPSHOTID + '\'')
    appendline_log('Restored server( '+str(label)+' ) with SUBID : ' + str(SUBID) + ' with SNAPSHOTID : ' + str(SNAPSHOTID) + ' .', 'RESTORE SNAPSHOT SERVER', 2)


def start_server(SUBID,label=None):
    os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/server/start --data \'SUBID=' + SUBID + '\'')
    appendline_log('Started server( '+str(label)+' ) with SUBID : ' + str(SUBID) + ' .', 'START SERVER', 2)


def change_ip_by_Label(Label,DCID=None):
    cur.execute('select * from Chains where Label=\''+Label+'\'')
    chain = cur.fetchone()
    if not chain:
        appendline_error('change_ip_by_Label(\''+str(Label)+'\',\''+str(DCID)+'\') - Chain not exists', 'CHANGE IP BY LABEL', 1)
        return
    server = get_server_by_SUBID(chain[2])
    if server != None and isinstance(server, dict) and server.__contains__('DCID') and server.__contains__('VPSPLANID') and server.__contains__('OSID') and server.__contains__('label'):
        SNAPSHOTID = chain[1]
        if SNAPSHOTID != None:
            # create new server
            if DCID == None:
                DCID = server['DCID']
            newserver = create_server(DCID, server['VPSPLANID'], server['OSID'], server['label'], SNAPSHOTID)
            if newserver == None:
                appendline_error('change_ip_by_Label(\''+str(Label)+'\',\''+str(DCID)+'\') - Failed to create a new server', 'CHANGE IP BY LABEL', 1)
                return
            try:
                cur.execute('update Chains set SUBID=\'' + newserver['SUBID'] + '\' where Label=\'' + Label + '\'')
                appendline_log('Updated Chain(' + str(Label) +')\'s SUBID to ' + str(newserver['SUBID']), 'CHANGE IP BY LABEL', 1)
                con.commit()
            except:
                con.rollback()
                try:
                    appendline_error('change_ip_by_Label(\''+str(Label)+'\',\''+str(DCID)+'\') - SUBID(' + str(newserver['SUBID']) + ')', 'CHANGE IP BY LABEL', 1)
                    return
                except:
                    appendline_error('change_ip_by_Label(\''+str(Label)+'\',\''+str(DCID)+'\') - newserver(' + str(newserver) + ')', 'CHANGE IP BY LABEL', 1)
                    return

            # destroy old server
            destroy_server(server['SUBID'], Label)

            #change aliyun domain record
            #change_record_ip_by_SUBID(chain[3],newserver['SUBID'])
        else:
            appendline_error('change_ip_by_Label(\''+str(Label)+'\',\''+str(DCID)+'\') - Failed to get SNAPSHOTID from database using Label - ' + str(chain[0]), 'CHANGE IP BY LABEL', 1)
    else:
        appendline_error('change_ip_by_Label(\''+str(Label)+'\',\''+str(DCID)+'\') - Failed to analysis server json with SUBID - ' + str(chain[2]), 'CHANGE IP BY LABEL', 1)


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
    regions = get_regions()
    regionslist = []
    index = 0
    for region in regions.keys():
        print(str(index+1)+'. '+regions[region]['name']+'  '+regions[region]['DCID'])
        regionslist.append(regions[region]['DCID'])
        index += 1
    selection=input('\nPlease select a region you would like to switch your server to(Default: same as old server): ')
    if selection == None or selection == '':
        change_ip_by_Label(Label)
    else:
        try:
            DCID = regionslist[int(selection)-1]
            cur.execute('Select * from Chains where Label=\''+Label+'\'')
            subid=cur.fetchone()[2]
            vpsplanid=get_VPSPLANID_by_SUBID(subid)
            if vpsplanid!=None and int(vpsplanid) in get_VPSPLAN_by_DCID(DCID):
                change_ip_by_Label(Label, DCID)
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
    try:
        j=json.loads(result)
        return j
    except:
        print('Something went wrong when trying to get json object from \'get_snapshots()\' function')
        appendline_error('get_snapshots() - result = ' + str(result), 'GET SNAPSHOTS', 2)
        return None



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


def create_snapshot(SUBID, label=None):
    results = os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/snapshot/create --data \'SUBID=' + SUBID + '\'')
    result = ''
    for line in results:
        result += line
    try:
        j=json.loads(result)
        appendline_log('Created a new snapshot( ' + str(label) + ' ) by SUBID( ' + str(SUBID) + ' )', 'CREATE SNAPSHOT', 2)
        return j
    except:
        print('Something went wrong when trying to create a new snapshot from \'create_snapshot(\''+SUBID+'\',\''+label+'\')\' function')
        appendline_error('create_snapshot(\''+str(SUBID)+'\',\''+str(label)+'\')', 'CREAT SNAPSHOT', 2)
        return None


def destroy_snapshot(SNAPSHOTID,label=None):
    os.popen('curl -H \'API-Key: ' + VULTR_KEY + '\' https://api.vultr.com/v1/snapshot/destroy --data \'SNAPSHOTID=' + SNAPSHOTID + '\'')
    appendline_log('Destroyed snapshot( '+str(label)+' ) with SNAPSHOTID '+str(SNAPSHOTID)+' .', 'DESTROY SNAPSHOT', 2)


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    Database
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
def add_chain_record(hierarchy=0):
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
    if servers==None or not isinstance(servers,dict):
        return None
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
        appendline_log('Created a new chain record. Label : '+str(Label)+'; SNAPSHOTID : '+str(SNAPSHOTID)+'; SUBID : '+str(SUBID)+'; RecordId : '+str(RecordId)+'; Status : '+str(stat), 'ADD CHAIN RECORD', hierarchy)
    except:
        print('Cannot create this record. Notice: Label, SNAPSHOTID, SUBID and REcordID are UNIQUE in database.')
        appendline_error('add_chain_record()', 'ADD CHAIN RECORD', hierarchy)
        con.rollback()


def delete_chain_record(hierarchy=0):
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
        appendline_log('Deleted chain record. Label: ' + Label, 'DELETE CHAIN RECORD', hierarchy)
    except:
        print('ERROR Input!\n')
        appendline_error('delete_chain_record', 'DELETE CHAIN RECORD', hierarchy)
        return

def check_status(SUBID,RecordId):
    if not ping('www.baidu.com'):
        return 'Unready'
    # ping ipv4
    server=get_server_by_SUBID(SUBID)
    if server==None or not isinstance(server,dict):
        return 'Unready'
    ipv4 = server['main_ip']
    if not tcpping(ipv4, CHECK_PORT):
        return 'Blocked'
    else:  # check domain record value
        try:
            if ipv4 != get_domain_record_by_RecordId(RecordId)['Value']:
                return 'Mismatch'
        except:
            return 'Unready'
    return 'Normal'

def check_chain_status_by_Label(Label):
    if not ping('www.baidu.com'):
        return 'Unready'
    cur.execute('select * from Chains where Label=\''+Label+'\'')
    chain = cur.fetchone()
    if chain:
        server=get_server_by_SUBID(chain[2])
        if server==None:
            return 'Server Not Exists'
        if server['status'] != 'active' or server['power_status'] != 'running' or server['server_state'] != 'ok':
            return 'Unready'
        #ping ipv4
        ipv4=server['main_ip']
        if not tcpping(ipv4, CHECK_PORT):
            return 'Blocked'
        else: #check domain record value
            try:
                if ipv4!=get_domain_record_by_RecordId(chain[3])['Value']:
                    return 'Mismatch'
            except:
                return 'Unready'
        return 'Normal'
        #ping domain
    else:
        return None

def check_chains():
    cur.execute('select * from Chains')
    chains = cur.fetchall()
    for chain in chains:
        try:
            cur.execute('update Chains set Status=\''+check_chain_status_by_Label(chain[0])+'\' where Label=\''+chain[0]+'\'')
            con.commit()
        except:
            con.rollback()
            print('Something went wrong when trying to update chain record')
            appendline_error('check_chains()', 'CHECK CHAINS', 0)


def repair_chain(Label, hierarchy=1):
    result = False
    status_now = check_chain_status_by_Label(Label)
    cur.execute('select * from Chains where Label=\''+Label+'\'')
    chain = cur.fetchone()
    status_past = chain[4]

    if status_past != 'Normal' and status_now == 'Normal':
        print('Chain(\'' + Label + '\') has been repaired')
        appendline_log('Repaired Chain( \'' + Label + '\' )', 'REPAIR CHAIN', hierarchy)
    elif status_now == 'Blocked':
        print('A blocked chain(\'' + Label + '\') has been detected! Repairing...')
        appendline_log('Detected blocked chain( \'' + Label + '\' )! Repairing...', 'REPAIR CHAIN', hierarchy)

        # same region
        if RANDOM_REGION == False:
            change_ip_by_Label(Label)
        else:
        # radom region
            flag_find = False
            new_region = choice(REGION_LIST)

            regions = get_regions()
            for region in regions.keys():
                if regions[region]['name'] == new_region:
                    change_ip_by_Label(Label, regions[region]['DCID'])
                    flag_find = True
                    break
            if flag_find = False:
                change_ip_by_Label(Label)
        result = True
    elif status_now == 'Mismatch':
        print('A mismatch chain(\'' + Label + '\') has been detected! Repairing...')
        appendline_log('Detected mismatch chain( \'' + Label + '\' )! Repairing...', 'REPAIR CHAIN', hierarchy)
        change_record_ip_by_SUBID(chain[3], chain[2])
        result = True
    elif status_now == 'Unready':
        result = True
    elif status_now == 'Server Not Exists':
        appendline_log('Lost server on chain( \'' + Label + '\' )!!!', 'REPAIR CHAIN', hierarchy)

    #update status
    try:
        cur.execute('update Chains set Status=\'' + status_now + '\' where Label=\'' + Label + '\'')
        con.commit()
    except:
        con.rollback()
        print('Something went wrong when trying to update chain record - ' + Label)
        appendline_error('repair_chain(\''+str(Label)+'\')', 'REPAIR CHAIN', hierarchy)

    return result

def repair_chains(hierarchy=1):
    print('---------------------Checking chains...---------------------')
    cur.execute('select * from Chains')
    chains = cur.fetchall()
    blocked = False
    #repair chains
    for chain in chains:
        if repair_chain(chain[0], hierarchy) == False:
            blocked = True

    #there are some chains still being blocked or not ready
    if blocked:
        check_int = CHECK_INTERVAL_MIN
    else:
        check_int = CHECK_INTERVAL_MAX

    # clean up irrelevant servers
    cur.execute('select * from Chains')
    chains = cur.fetchall()
    servers = get_servers()
    if servers == None or not isinstance(servers, dict):
        print('---------------------All chains have been checked---------------------')
        return None
    find=False
    for server in servers.keys():
        find = False
        for chain in chains:
            if servers[server]['SUBID'] == chain[2]:
                find = True
                break
        if not find:
            destroy_server(servers[server]['SUBID'])
    print('---------------------All chains have been checked---------------------')


'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
                                                    threading
'''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
runflag=False


def monitoring():
    print('Start Monitor Chains')
    while True:
        for i in range(0, check_int):
            for j in range(0, 60):
                time.sleep(1)
        repair_chains()
        print('#Last Check time: '+get_now()+'#\n')
        show_chains()
        show_menu()
        print('Please select: ')


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
    if tcpping(str(server['main_ip']),CHECK_PORT):
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
    if servers==None or not isinstance(servers,dict):
        return None
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
