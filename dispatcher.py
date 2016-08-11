# -*- coding: utf-8 -*-
import logging
import logging.config

logging.config.fileConfig("logger.cfg")
logger = logging.getLogger("main")

import netrc
import configparser
import re
import time
import sys
def get_section_by_package(package,config):
    '''从config中找出匹配PACKAGE的section. config是ConfigParser.read后的结果'''
    for section in config.sections():
        reg = re.compile(section)
        if reg.match(package):
            return section

def get_ftp_info_by_package(package,cfg_file,netrc_file=None):
    '''根据PACKAGE,从CFG_FILE及NETRC_FILE中找出对应ftp的HOST,LOGIN,ACCOUNT以及PASSWORD

    return host,login,account,password,dest_dir,install_command'''
    config = configparser.ConfigParser()
    config.read(cfg_file)
    section = get_section_by_package(package,config)
    if not section:
        logger.warning("%s中未找到匹配%s的section",cfg_file,package)
        exit(-1)
    else:
        try:
            netrc_info = netrc.netrc(netrc_file)
            login,account,password = netrc_info.authenticators(host)
        except Exception:
            login,account,password = None,None,None
        host = config.get(section,"host")
        login = config.get(section,"login",fallback=None) or login
        account = config.get(section,"account",fallback=None) or account
        password = config.get(section,"password",fallback=None) or password
        dest_dir = config.get(section,"dest_dir",fallback=None) or "~/newcx/{0}".format(time.strftime("%Y%m%d_%H%M%S"))
        install_command = config.get(section,"install_command",fallback=None)
    return host,login,account,password,dest_dir,install_command

import ftplib
import os.path

def upload_by_ftp(file_path,host,dest_dir,login="anonymous",password="",account=""):
    '''upload FILE_PATH to DEST_DIR in HOST,though ftp protocol'''
    with ftplib.FTP(host=host,user=login,passwd=password,acct=account) as ftp:
        ftp.set_debuglevel(2)   # A value of 2 or higher produces the maximum amount of debugging output, logging each line sent and received on the control connection.
        logger.debug(ftp.getwelcome())
        try:
            ftp.mkd(dest_dir)       # 创建目标文件夹
        except ftplib.error_perm:
            logger.debug("%s:%s already exist",host,dest_dir)
        ftp.cwd(dest_dir)       # 进入目标文件夹
        with open(file_path,"rb") as file_handler:
            ftp.storbinary("STOR {0}".format(os.path.basename(file_path)), file_handler)
    logger.debug("ftp {0} to {1}:{2} done".format(file_path,host,dest_dir))

try:
    import pexpect
    def upload_by_scp (file_path,host,dest_dir,login,password):
        '''upload FILE_PATH to DEST_DIR in HOST,by scp program'''
        scp_command = "scp {0} {1}@{2}:{3}/".format(file_path,login,host,dest_dir)
        logger.debug("execute:%s",scp_command)
        p = pexpect.spawn(scp_command)
        while(p.isalive()):
            idx = p.expect(['yes/no','password'])
            if idx == 0:
                p.sendline("yes")
            else:
                p.sendline(password)
except Exception:
    import pty
    import subprocess
    def upload_by_scp (file_path,host,dest_dir,login,password):
        execute_remote_command_by_ssh(host,login,password,"mkdir -p {}".format(dest_dir))
        scp_command = "echo {4} |python3 pty-process.py scp {0} {1}@{2}:{3}/".format(file_path,login,host,dest_dir,password)
        result = subprocess.check_output(scp_command,shell=True)
        return result

def upload(file_path,host,dest_dir,login,password):
    '''upload FILE_PATH to DEST_DIR in HOST'''
    try:
        upload_by_scp(file_path,host,dest_dir,login,password)
    except:
        upload_by_ftp(file_path,host,dest_dir,login,password)

try:
    import pexpect
    def execute_remote_command_by_ssh(host,login,password,command):
        ssh_command = "ssh {}@{} {}".format(password,login,host,command)
        logger.debug("execute:%s",ssh_command)
        p = pexpect.spawn(ssh_command)
        while(p.isalive()):
            idx = p.expect(['yes/no','password'])
            if idx == 0:
                p.sendline("yes")
            else:
                p.sendline(password)
except Exception:
    def execute_remote_command_by_ssh(host,login,password,command):
        ssh_command = "echo {} | python3 pty-process.py ssh {}@{} '{}'".format(password,login,host,command)
        logger.debug("execute:%s",ssh_command)
        result = subprocess.check_output(ssh_command,shell=True)
        logger.debug("result:%s",result)
        return result

def dispatch_file(file_path,cfg_file="general-dispatch-info.cfg",netrc_file=None):
    package = os.path.basename(file_path)
    host,login,account,password,dest_dir,install_command = get_ftp_info_by_package(package,cfg_file,netrc_file)
    upload(file_path,host,dest_dir,login,password)
    if install_command:
        execute_remote_command_by_ssh(host,login,password,install_command)

import threading
def dispatch_files(file_paths,cfg_file="general-dispatch-info.cfg",netrc_file=None):
    threads = (threading.Thread(target-dispatch_file,args=(file_path,cfg_file,netrc_file)) for file_path in file_paths)
    for thread in threads:
        thread.start()
    return threads

if __name__ == "__main__":
    if len(sys.argv) == 2:
        dispatch_file(sys.argv[1])
    else:
        dispatch_files(sys.argv[1:])
