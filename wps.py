# -*- coding: utf-8 -*-

import os
import subprocess

def get_stdout(cmdline):
    return subprocess.check_output(cmdline, shell=True)

def kill_process_and_exit(pid):
    returncode = os.system('taskkill /pid {:}'.format(pid))
    exit(returncode)

def term_process_and_exit(pid):
    returncode = os.system('taskkill /f /pid {:}'.format(pid))
    exit(returncode)

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
keywords    = args.keyword
line_format = args.format
use_desc    = args.desc
killtarget  = args.kill
termtarget  = args.terminate

if killtarget and killtarget.isdigit():
    pid = int(killtarget)
    kill_process_and_exit(pid)
if termtarget and termtarget.isdigit():
    pid = int(termtarget)
    term_process_and_exit(pid)

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

# wmic process の出力結果をパース.

processes = []
process = None
for i,line in enumerate(stdout_lines):
    if i%attrs_count==0:
        if i!=0:
            processes.append(process)
        process = Process()
    process.parse_line(line)
processes.append(process) # The last instance.

# 結果表示や絞り込みで使うための整形

outlines = []
outprocesses = []
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
    outprocesses.append(process)

# pkill 時は当該 PID を特定して（あるいはさせて） kill して終わり.

if killtarget or termtarget:
    query = killtarget
    use_term = False
    if query==None:
        query = termtarget
        use_term = True

    target_candidates = []
    candidate_curno = 0
    for i,ps in enumerate(outprocesses):
        findee = '{:>5} {:} {:}'.format(ps.pid, ps.caption, ps.commandline)
        findee = findee.lower()
        if findee.find(query)==-1:
            continue
        # 1-origin at displaying,
        candidate_curno += 1
        p('{:>2} {:}'.format(candidate_curno, findee))
        target_candidates.append(ps.pid)

    if len(target_candidates)==0:
        abort('No mached process with "{:}".'.format(query))

    if len(target_candidates)==1:
        pid = target_candidates[0]
        if use_term:
            term_process_and_exit(pid)
        kill_process_and_exit(pid)

    # 候補複数の時は番号で一つを選ばせる.
    # q でキャンセル or 一つ選ぶまで終わらせない.

    pid = None
    while True:
        s = raw_input('Target PID? (Press "q" to cancel.) >')
        s = s.lower()
        if s=='q':
            exit(0)
        if s.isdigit():
            # 0-origin at internal.
            idx = int(s) - 1
            if idx<0 or idx>=len(target_candidates):
                continue
            pid = target_candidates[idx]
            break
        continue
    if use_term:
        term_process_and_exit(pid)
    kill_process_and_exit(pid)

# それ以外はただの表示処理なので絞りこんで表示して終わり.

# 並びに統一性をもたせるためソートをかます.
# ASC/DESC はオプションで切り替えてもらう.
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

