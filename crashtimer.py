#!/usr/bin/python

import sys
import os
from os import listdir
from os.path import isfile, join
import zipfile
import os.path
import gzip
import datetime


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DIM = '\033[2m'
    WHITE = '\033[1m\033[37m'


def fnTimeStr(tt):
    ms = sec = mm = hh = dd = 0
    ms = tt % 1000
    timestr = "%d ms" % (ms)
    if tt >= 1000:
        sec = (tt / 1000) % 60
        timestr = "%d Sec, %d ms" % (sec, ms)
    if tt >= 60000:
        mm = (tt / 60000) % 60
        timestr = "%d Mins, %d Sec, %d ms" % (mm, sec, ms)
    if tt >= 3600000:
        hh = (tt / 3600000) % 24
        timestr = "%d H, %d Mins, %d Sec, %d ms" % (hh, mm, sec, ms)
    if tt >= 24 * 3600000:
        dd = tt / (24 * 3600000)
        timestr = "%d Day, %d H, %d Mins, %d Sec, %d ms" % (
            dd, hh, mm, sec, ms)
    return timestr


def fnUnZip(source_filename, dest_dir):
    outfilename = source_filename.rstrip(".gz")
    inF = gzip.open(source_filename, 'rb')
    open(outfilename, 'w').write(inF.read())
    inF.close()
    # print "unzip: "+ outfilename


def fnFindAllzipArchAndUzip(flist, path):
    zipArch = ['.gz', '.zip', '.rar', '.7z']
    for target_file in flist:
        for j in zipArch:
            if j in target_file:
                fnUnZip(path + "/" + target_file, path)
                break


def fnOpenAndReadFirstLine(fileName):
    with open(fileName, 'r') as inf:
        line = inf.readline().rstrip()
        line = line.lstrip('Process:')
    return line


def fnGenTimeTable(fname):
    time = fname
    if fname.endswith("txt"):
        for p in errorPattern:
            if p in fname:
                time = fname.lstrip(p + '@')
                time = time.rstrip('.txt')
                dictTimeTable[time] = p
                break


def fnFilterCriticalCheckPoint(fname):
    result = 0
    if fname.endswith("txt"):
        for p in errorPattern:
            if p in fname:
                result = 1
                break
    return result


def fnFilterSystemServerCrash(fname):
    result = 0
    if fname.endswith("txt"):
        if 'system_server_crash' in fname:
            result = 1
    return result


def fnFilterSystemNativeCrash(fname):
    result = 0
    if fname.endswith("txt"):
        if 'SYSTEM_TOMBSTONE' in fname:
            result = 1
    return result


def fnFilterSystemAppWtf(fname):
    result = 0
    if fname.endswith("txt"):
        if 'system_app_wtf' in fname:
            result = 1
    return result


def fnFilterSystemCrash(fname):
    result = 0
    if fname.endswith("txt"):
        if 'system_app_crash' in fname:
            result = 1
    return result


def fnFilterSystemAnr(fname):
    result = 0
    if fname.endswith("txt"):
        if 'system_app_anr' in fname:
            result = 1
    return result


def fnAddToDict(inDic, itemName):
    if itemName in inDic:
        inDic[itemName] += 1
    else:
        inDic[itemName] = 1


def fnGetNativeCrashName(fpath):
    with open(fpath, 'r') as fp:
        for line in fp:
            if '>>>' and '<<<' in line:
                start = line.find('>>>', 0, len(line))
                end = line.find('<<<', 0, len(line))
                return line[start + 4:end - 1]


def fnGetDropboxDirList(rootpath):
    dirs = [iti[0] for iti in os.walk(rootpath)]
    return [dropboxdir for dropboxdir in dirs if ("dropbox" in dropboxdir or "Dropbox" in dropboxdir)]


def fnParsDropbox(pathDropbox):

    print bcolors.WHITE + "\n=== Summary of : " + pathDropbox + " ===" + bcolors.ENDC
    # Unzip
    filelist = [f for f in listdir(
        pathDropbox) if isfile(join(pathDropbox, f))]
    fnFindAllzipArchAndUzip(filelist, pathDropbox)
    filelist = [f for f in listdir(
        pathDropbox) if isfile(join(pathDropbox, f))]

    CriticalEvents = filter(fnFilterCriticalCheckPoint, filelist)
    for itm in CriticalEvents:
        fnGenTimeTable(itm)

    # Get log time table
    print bcolors.WHITE + "\nHistory:" + bcolors.ENDC
    prvTime = 0
    for time in sorted(dictTimeTable):
        intervel = int(time) - prvTime
        if prvTime > 0:
            if intervel > 120000:
                print bcolors.ENDC+bcolors.DIM + '    ++ ' + fnTimeStr(int(time) - prvTime) + bcolors.ENDC
            else:
                print bcolors.WARNING + '    ++ ' + fnTimeStr(int(time) - prvTime)
        # print '  '+dictTimeTable[time], time
        if ('SYSTEM_LAST_KMSG' in dictTimeTable[time] or 'system_server_watchdog' in dictTimeTable[time] or 'SYSTEM_RESTART' in dictTimeTable[time]  or 'FRAMEWORK_REBOOT' in dictTimeTable[time]):
            print bcolors.FAIL
        print '  ' + dictTimeTable[time], datetime.datetime.fromtimestamp(int(time) / 1000).strftime('%x %X')
        prvTime = int(time)

    # Get System server Crashs
    SystemAppServerCrashes = filter(fnFilterSystemServerCrash, filelist)
    if len(SystemAppServerCrashes) > 0:
        print bcolors.WHITE + "\nSystem Server Crash:" + bcolors.ENDC
        for item in SystemAppServerCrashes:
            fnAddToDict(dictServerCrash, fnOpenAndReadFirstLine(
                pathDropbox + "/" + item))
        for item in sorted(dictServerCrash, key=dictServerCrash.get, reverse=True):
            print '  ' + str(dictServerCrash[item]), item

    # Get System App Native Crashs
    SystemAppNativeCrashes = filter(fnFilterSystemNativeCrash, filelist)
    if len(SystemAppNativeCrashes) > 0:
        print bcolors.WHITE + "\nSystem app Native Crash:" + bcolors.ENDC
        for item in SystemAppNativeCrashes:
            fnAddToDict(dictNative, fnGetNativeCrashName(
                pathDropbox + "/" + item))
        for item in sorted(dictNative, key=dictNative.get, reverse=True):
            print '  ' + str(dictNative[item]), item

    # Get System App Crashes
    SystemAppCrashes = filter(fnFilterSystemCrash, filelist)
    if len(SystemAppCrashes) > 0:
        print bcolors.WHITE + "\nSystem app crashes:" + bcolors.ENDC
        for item in SystemAppCrashes:
            fnAddToDict(dictCrash, fnOpenAndReadFirstLine(
                pathDropbox + "/" + item))

        for item in sorted(dictCrash, key=dictCrash.get, reverse=True):
            print '  ' + str(dictCrash[item]), item

    # Get System App WTF
    SystemAppWTF = filter(fnFilterSystemAppWtf, filelist)
    if len(SystemAppWTF) > 0:
        print bcolors.WHITE + "\nSystem app WTF:" + bcolors.ENDC
        for item in SystemAppWTF:
            fnAddToDict(dictSysappWTF, fnOpenAndReadFirstLine(
                pathDropbox + "/" + item))
        for item in sorted(dictSysappWTF, key=dictSysappWTF.get, reverse=True):
            print '  ' + str(dictSysappWTF[item]), item

    # Get System App ANR
    SystemAppAnr = filter(fnFilterSystemAnr, filelist)
    if len(SystemAppAnr) > 0:
        print bcolors.WHITE + "\nSystem app ANR:" + bcolors.ENDC
        for item in SystemAppAnr:
            fnAddToDict(dictANR, fnOpenAndReadFirstLine(
                pathDropbox + "/" + item))

        for item in sorted(dictANR, key=dictANR.get, reverse=True):
            print '  ' + str(dictANR[item]), item
        print bcolors.ENDC


dictServerCrash = dict()
dictCrash = dict()
dictANR = dict()
dictNative = dict()
dictTimeTable = dict()
dictSysappWTF = dict()

currentdir = os.path.dirname(os.path.abspath(__file__))
errorPattern = ['KERNEL_PANIC', 'system_server_watchdog', 'FRAMEWORK_REBOOT','SYSTEM_LAST_KMSG',
                'SYSTEM_BOOT', 'system_server_crash', 'system_server_wtf', 'SYSTEM_RESTART', 'system_app_crash', 'system_app_anr']
#pathDropbox = str(sys.argv[1])
pathRoot = str(sys.argv[1])

# list all dropbox path
dropboxList = fnGetDropboxDirList(pathRoot)

# parse each dropboxList ...
for box in dropboxList:
    fnParsDropbox(box)
