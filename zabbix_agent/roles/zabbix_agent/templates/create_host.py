#!/usr/bin/env python
# -*- coding: utf-8 -*-

# 本脚本用于在zabbix中创建指定主机并关联到指定模板

import sys, json, urllib2

# zabbix api的地址
url = '{{zabbix_api_url}}'
# 用于登录zabbix的用户和密码
user = '{{zabbix_user}}'
password = '{{zabbix_password}}'
# 要添加的主机
prefix = '{{prefix}}'
host_ip = '{{inventory_hostname}}'
hostname = prefix + host_ip
# 主机所属的主机组
hostgroup = '{{hostgroup}}'
# 要关联的模板名称
templates = {{templates}}


# 用于访问zabbix api的函数。返回从zabbix获取到的反系列化后的数据。
# 可能出现的异常为：urllib2.URLError
def access_zabbix(f_method,f_params,f_count,f_token):
    method, params, count, token = f_method, f_params, f_count, f_token

    # 报头字段
    header ={'Content-Type':'application/json-rpc'}

    # 拼装post请求数据
    data = {'jsonrpc':'2.0', 'method':method, 'params':params, 'id':count, 'auth':token}
    # 系列化为json数据
    data_json = json.dumps(data)

    # 创建Request object
    request = urllib2.Request(url,data_json)
    # 往Request Object中添加报头字段
    for key in header:
        request.add_header(key,header[key])

    try:
        # urlopen( )函数发起URL请求，并返回一个file-like object
        raw_response = urllib2.urlopen(request)
        # 使用read( )方法读取file-like object的内容(本例中是一个json对象)，并使用json.loads( )将其反系列化
        result_dict = json.loads(raw_response.read( ))
    finally:
        if ('raw_response' in vars( )):              # 判断变量raw_response是否存在
            raw_response.close( )                # 对file-like object调用close( )函数，释放资源

    return result_dict


# 用于登录zabbix的函数。返回结果为token值。
# 可能出现的异常为：urllib2.URLError
def login(f_count):
    count = f_count
    method = 'user.login'
    params = {'user':user, 'password':password}
    token = None

    response_dict = access_zabbix(method,params,count,token)
    if ( 'result' in response_dict ):
        print '[INFO] Login zabbix succeeds.'
        return response_dict['result']
    else:
        print '[ERROR] Login zabbix fails.'
        print '[ERROR]', response_dict['error']['message'], response_dict['error']['data']
        sys.exit(1)


# 用于登出zabbix的函数。返回结果为None。
# 可能出现的异常为：urllib2.URLError
def logout(f_count,f_token):
    count, token = f_count, f_token
    method = 'user.logout'
    params = [ ]

    response_dict = access_zabbix(method,params,count,token)
    if ( 'result' in response_dict ):
        print '[INFO] Logout zabbix succeeds.'
    else:
        print '[ERROR] Logout zabbix fails.'
        print '[ERROR] Token %s unreleased' % token
        print '[ERROR]', response_dict['error']['message'], response_dict['error']['data']
        sys.exit(1)


# 用于操作(获取信息/设置)zabbix的函数。返回获取到的信息或操作结果。
# 可能出现的异常为：urllib2.URLError
def operation(f_method,f_params,f_count,f_token):
    method, params, count, token = f_method, f_params, f_count, f_token

    response_dict = access_zabbix(method,params,count,token)
    if ( 'result' in response_dict ):
        return response_dict['result']
    else:
        print '[ERROR] Operating fails.'
        print '[ERROR]', response_dict['error']['message'], response_dict['error']['data']
        count += 1
        logout(count,token)
        sys.exit(1)


# 程序主体逻辑。返回结果为None。
# 可能出现的异常为：urllib2.URLError
def process_logic( ):
    count = 1

    # 登录并获取token
    token = login(count)

    # 获取主机信息
    method = 'host.get'
    params = {'output':['hostid','host'],'filter':{'host':hostname}}
    count += 1
    result = operation(method,params,count,token)

    if result:
        print '[INFO] Host "%s" already exists in the zabbix. No need to add it again.' % hostname
        count += 1
        logout(count,token)
        sys.exit(0)

    # 获取主机组信息
    method = 'hostgroup.get'
    params = {'output':['groupid','name'],'filter':{'name':hostgroup}}
    count += 1
    result = operation(method,params,count,token)

    if not result:
        print '[ERROR] Host group "%s" does not exist.' % hostgroup
        count += 1
        logout(count,token)
        sys.exit(1)
    else:
        groupid = result[0]['groupid']

    # 获取模板信息
    templates_id = [ ]
    for template in templates:
        method = 'template.get'
        params = {'output':['templateid','host'],'filter':{'host':template}}
        count += 1
        result = operation(method,params,count,token)
        
        if not result:
            print '[ERROR] Template "%s" does not exist.' % template
            count += 1
            logout(count,token)
            sys.exit(1)
        else:
            templates_id.append({'templateid':result[0]['templateid']})

    # 创建主机并关联模板
    method = 'host.create'
    params = {
              'host':hostname,
              'interfaces':[{'type':1, 'main':1, 'useip':1, 'ip':host_ip, 'dns':'', 'port':'10050'}],
              'groups':[{'groupid':groupid}],
              'templates':templates_id
             }
    count += 1
    result = operation(method,params,count,token)

    if 'hostids' in result:
        print '[INFO] Creating host "%s" in zabbix succeeds.' % hostname
    else:
        print '[ERROR] Creating host "%s" in zabbix fails.' % hostname
        print '[ERROR]', result
        count += 1
        logout(count,token)
        sys.exit(1)

    # 退出登录
    count += 1
    logout(count,token)


def main( ):
    try:
        process_logic( )
    except urllib2.URLError as e:
        print '[Exception URLError]:', e
        sys.exit(1)


main( )
