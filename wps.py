# -*- coding: utf-8 -*-

import os
import subprocess

def get_stdout(cmdline):
    return subprocess.check_output(cmdline, shell=True)

def p(msg):
    print msg

def abort(msg):
    p('Error:{:}'.format(msg))
    exit(1)

def parse_arguments():
    import argparse

    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('keyword', default='', nargs='*',
        help='Keywords to extract lines with lowercase-AND partial search.')

    parser.add_argument('-f', '--format', default='p l', type=str,
        help='A combination of p=PID, d=creationDate, c=Caption and l=commandLine')
    parser.add_argument('--desc', default=False, action='store_true',
        help='Use DESC order. If not given, use ASC order.')

    parser.add_argument('-k', '--kill', default=None, type=str,
        help='A PID or keyword of process being killed.')
    parser.add_argument('-t', '--terminate', default=None, type=str,
        help='A PID or keyword of process being killed forcely.')

    return parser.parse_args()

args = parse_arguments()
keywords     = args.keyword
line_format = args.format
use_desc    = args.desc
killtarget  = args.kill
termtarget  = args.terminate

if killtarget and killtarget.isdigit():
    kill_pid = int(killtarget)
    returncode = os.system('taskkill /pid {:}'.format(kill_pid))
    exit(returncode)
if termtarget and termtarget.isdigit():
    term_pid = int(termtarget)
    returncode = os.system('taskkill /f /pid {:}'.format(term_pid))
    exit(returncode)

selfpid = os.getpid()

attrs = 'COMMANDLINE,PROCESSID,CREATIONDATE,CAPTION'
attrs_count = len(attrs.split(','))
commandline = 'wmic process get {:} /FORMAT:LIST'.format(attrs)

stdout_raw = get_stdout(commandline)
stdout_lines = stdout_raw.split('\r\n')
# remove blank lines.
stdout_lines = [line for line in stdout_lines if len(line.strip())!=0]
# remove each lines's line-break. (Not \r\n but \n)
stdout_lines = [line[:-1] for line in stdout_lines]

# [Original Format]
# Caption=PyScripter.exe
# CommandLine="D:\bin\PyScripter\PyScripter.exe" "D:\work\github\stakiran\wps\wps.py"
# CreationDate=20170914094116.104179+540
# ProcessId=3120
class Process:
    def __init__(self):
        pass

    def parse_line(self, line):
        if line.find('=')==-1:
            abort('Invalid "wmic process" format: "{:}"'.format(line))
        k, v = line.split('=', 1)

        k = k.lower()
        setter = None
        setter_dict = {
            'caption'      : self.set_caption,
            'commandline'  : self.set_commandline,
            'creationdate' : self.set_date,
            'processid'    : self.set_pid,
        }
        setter = setter_dict[k]
        setter(v)

    def set_caption(self, caption):
        self._caption = caption

    def set_commandline(self, commandline):
        self._commandline = commandline

    def set_date(self, creationdate):
        d = creationdate

        # BEFORE: 20170914094116.104179+540
        # AFTER : 2017/09/14 09:41:16

        self._date = '{:}/{:}/{:} {:}:{:}:{:}'.format(
            d[0:4], d[4:6], d[6:8], d[8:10], d[10:12], d[12:14]
        )

    def set_pid(self, pid_by_str):
        self._pid = int(pid_by_str)

    @property
    def pid(self):
        return self._pid

    @property
    def commandline(self):
        return self._commandline

    @property
    def caption(self):
        return self._caption

    @property
    def date(self):
        return self._date

processes = []
process = None
for i,line in enumerate(stdout_lines):
    if i%attrs_count==0:
        if i!=0:
            processes.append(process)
        process = Process()
    process.parse_line(line)
processes.append(process) # The last instance.

outlines = []
for i,process in enumerate(processes):
    # 自身のプロセス情報は除外する.
    if process.pid == selfpid:
        continue

    line = line_format
    # 直に replace すると他の値まで置換しちゃうので
    # まずは「どの値にも現れないであろう文字」を入れた文字列に置換して,
    # それからそいつを置換することで回避.
    line = line.replace('p' , '|p|')
    line = line.replace('d' , '|d|')
    line = line.replace('c' , '|c|')
    line = line.replace('l' , '|l|')
    line = line.replace('|p|', '{:>5}'.format(process.pid))
    line = line.replace('|d|', process.date)
    line = line.replace('|c|', process.caption)
    line = line.replace('|l|', process.commandline)
    outlines.append(line)

outlines.sort()
if use_desc:
    outlines.reverse()

def be_extracted(line, keywords):
    # All extrcted because no keyword.
    if len(keywords)==0:
        return True

    filteree = line.lower()
    for keyword in keywords:
        q = keyword.lower()
        if filteree.find(q)==-1:
            return False
    return True

for line in outlines:
    if be_extracted(line, keywords):
        p(line)

exit(0)

