import logging
import logging.handlers
LOGGING_FILE = "auto-dispatcher.log"
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
fh = logging.handlers.RotatingFileHandler(LOGGING_FILE,maxBytes=18*1024*1024,backupCount=5)
formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

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

# import pty
# import subprocess
# def upload_by_scp_in_pty (file_path,host,dest_dir,login,password):
#     # scp_command = "scp {0} {1}@{2}:{3}/".format(file_path,login,host,dest_dir)
#     remote_dest_dir = "{0}@{1}:{2}/".format(login,host,dest_dir)
#     p = subprocess.Popen(["pty-process.py" "scp", file_path, remote_dest_dir], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
#     result = p.communicate(password)
#     p.wait()
#     return result

def upload(file_path,host,dest_dir,login,password):
    '''upload FILE_PATH to DEST_DIR in HOST'''
    try:
        upload_by_scp(file_path,host,dest_dir,login,password)
    except:
        upload_by_ftp(file_path,host,dest_dir,login,password)

def execute_remote_command_by_ssh(host,login,password,command):
    ssh_command = "ssh {0}@{1} command"
    logger.debug("execute:%s",ssh_command)
    p = pexpect.spawn(ssh_command)
    while(p.isalive()):
        idx = p.expect(['yes/no','password'])
        if idx == 0:
            p.sendline("yes")
        else:
            p.sendline(password)

def dispatch(file_path,cfg_file="general-dispatch-info.cfg",netrc_file=None):
    package = os.path.basename(file_path)
    host,login,account,password,dest_dir,install_command = get_ftp_info_by_package(package,cfg_file,netrc_file)
    upload(file_path,host,dest_dir,login,password)
    if install_command:
        execute_remote_command_by_ssh(host,login,password,install_command)
