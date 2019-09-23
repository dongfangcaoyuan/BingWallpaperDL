#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time
import logging
import logging.handlers
import platform
import errno

if platform.system() == 'Windows':
    from ctypes import windll, c_ulong

    def color_text_decorator(function):
        def real_func(self, string):
            windll.Kernel32.GetStdHandle.restype = c_ulong
            h = windll.Kernel32.GetStdHandle(c_ulong(0xfffffff5))
            if function.__name__.upper() == 'ERROR':
                windll.Kernel32.SetConsoleTextAttribute(h, 12)
            elif function.__name__.upper() == 'WARN':
                windll.Kernel32.SetConsoleTextAttribute(h, 13)
            elif function.__name__.upper() == 'INFO':
                windll.Kernel32.SetConsoleTextAttribute(h, 14)
            elif function.__name__.upper() == 'DEBUG':
                windll.Kernel32.SetConsoleTextAttribute(h, 15)            
            else:
                windll.Kernel32.SetConsoleTextAttribute(h, 15)
            function(self, string)
            windll.Kernel32.SetConsoleTextAttribute(h, 15)
        return real_func
else:
    def color_text_decorator(function):
        def real_func(self, string):
            if function.__name__.upper() == 'ERROR':
                self.stream.write('\033[0;31;40m')
            elif function.__name__.upper() == 'WARN':
                self.stream.write('\033[0;33;40m')
            elif function.__name__.upper() == 'INFO':
                self.stream.write('\033[0;35;40m')
            elif function.__name__.upper() == 'DEBUG':
                self.stream.write('\033[0;37;40m')            
            else:
                self.stream.write('\033[0;35;40m')
            function(self, string)
            self.stream.write('\033[0m')
        return real_func

FORMAT = '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'


class FileLockException(Exception):
    pass


class FileLock(object):
    """ A file locking mechanism that has context-manager support so 
        you can use it in a with statement. This should be relatively cross
        compatible as it doesn't rely on msvcrt or fcntl for the locking.
    """

    def __init__(self, file_name, timeout=10, delay=.05):
        """ Prepare the file locker. Specify the file to lock and optionally
            the maximum timeout and the delay between each attempt to lock.
        """
        self.is_locked = False
        self.lockfile = os.path.join(os.getcwd(), "%s.lock" % file_name)
        self.file_name = file_name
        self.timeout = timeout
        self.delay = delay

    def acquire(self):
        """ Acquire the lock, if possible. If the lock is in use, it check again
            every `wait` seconds. It does this until it either gets the lock or
            exceeds `timeout` number of seconds, in which case it throws 
            an exception.
        """
        start_time = time.time()
        while True:
            try:
                # 独占式打开文件
                self.fd = os.open(self.lockfile, os.O_CREAT |
                                  os.O_EXCL | os.O_RDWR)
                break
            except OSError as e:
                if e.errno != errno.EEXIST:
                    raise
                if (time.time() - start_time) >= self.timeout:
                    raise FileLockException("Timeout occured.")
                time.sleep(self.delay)
        self.is_locked = True

    def release(self):
        """ Get rid of the lock by deleting the lockfile. 
            When working in a `with` statement, this gets automatically 
            called at the end.
        """
        # 关闭文件，删除文件
        if self.is_locked:
            os.close(self.fd)
            os.unlink(self.lockfile)
            self.is_locked = False

    def __enter__(self):
        """ Activated when used in the with statement. 
            Should automatically acquire a lock to be used in the with block.
        """
        if not self.is_locked:
            self.acquire()
        return self

    def __exit__(self, type, value, traceback):
        """ Activated at the end of the with statement.
            It automatically releases the lock if it isn't locked.
        """
        if self.is_locked:
            self.release()

    def __del__(self):
        """ Make sure that the FileLock instance doesn't leave a lockfile
            lying around.
        """
        self.release()


class SafeRotatingFileHandler(logging.handlers.TimedRotatingFileHandler):
    """Override doRollover lines commanded by "##" is changed by cc
    """

    def __init__(self, filename, when='h', interval=1, backupCount=0, encoding=None, delay=False, utc=False):
        logging.handlers.TimedRotatingFileHandler.__init__(
            self, filename, when, interval, backupCount, encoding, delay, utc)

    def doRollover(self):
        """
        do a rollover; in this case, a date/time stamp is appended to the filename
        when the rollover happens.  However, you want the file to be named for the
        start of the interval, not the current time.  If there is a backup count,
        then we have to get a list of matching filenames, sort them and remove
        the one with the oldest suffix.

        Override,   1. if dfn not exist then do rename
                    2. _open with "a" model
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        # get the time that this sequence started at and make it a TimeTuple
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)
        dfn = self.baseFilename + "." + time.strftime(self.suffix, timeTuple)
        # if os.path.exists(dfn):
        # os.remove(dfn)
        # Issue 18940: A file may not have been created if delay is True.
        # if os.path.exists(self.baseFilename):
        if not os.path.exists(dfn) and os.path.exists(self.baseFilename):
            with FileLock(self.baseFilename):
                os.rename(self.baseFilename, dfn)
        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        if not self.delay:
            self.mode = "a"
            self.stream = self._open()
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        # If DST changes and midnight or weekly rollover, adjust for this.
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:  # DST kicks in before next rollover, so we need to deduct an hour
                    addend = -3600
                else:           # DST bows out before next rollover, so we need to add an hour
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt


class MainLogger(object):
    DEBUG_MODE = True
    LOG_LEVEL = 5

    def __init__(self, name):
        current_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'logs')
        if not os.path.exists(current_path):
            os.makedirs(current_path)

        # baseconfig
        logging.basicConfig()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(FORMAT)

        # th_all = logging.handlers.TimedRotatingFileHandler(os.path.join(
        #     current_path, 'slave_main_atc.log'), when='M', interval=1, backupCount=7)
        # th_all.setFormatter(formatter)
        # th_all.setLevel(logging.DEBUG)
        # self.logger.addHandler(th_all)

        fh = logging.FileHandler(os.path.join(
            current_path, 'common_log.log'), 'a')
        fh.setFormatter(formatter)
        fh.setLevel(logging.DEBUG)
        self.logger.addHandler(fh)
        self.logger.propagate = 0

        # 防止终端重复打印
        self.logger.propagate = 0

    def hint(self, string):
        # 去除多余连续空格
        strTmp = str(string)
        strTmp = ' '.join(strTmp.split())
        if self.LOG_LEVEL >= 5:
            return self.logger.debug(strTmp)
        else:
            pass

    def debug(self, string):
        # 去除多余连续空格
        strTmp = str(string)
        strTmp = ' '.join(strTmp.split())
        if self.LOG_LEVEL >= 4:
            return self.logger.debug(strTmp)
        else:
            pass

    def info(self, string):
        # 去除多余连续空格
        strTmp = str(string)
        strTmp = ' '.join(strTmp.split())
        if self.LOG_LEVEL >= 3:
            return self.logger.info(strTmp)
        else:
            pass

    def warn(self, string):
        # 去除多余连续空格
        strTmp = str(string)
        strTmp = ' '.join(strTmp.split())
        if self.LOG_LEVEL >= 2:
            return self.logger.warning(strTmp)
        else:
            pass

    def error(self, string):
        # 去除多余连续空格
        strTmp = str(string)
        strTmp = ' '.join(strTmp.split())
        if self.LOG_LEVEL >= 1:
            return self.logger.error(strTmp)
        else:
            pass

main_logger = MainLogger('SlaveMainLogger')


class Logger(object):
    DEBUG_MODE = True
    LOG_LEVEL = 5

    def __init__(self, name, filename=None):

        self.name = name
        # baseconfig
        logging.basicConfig()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(FORMAT)

        # output to terminal
        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        sh.setLevel(logging.DEBUG if self.DEBUG_MODE else logging.INFO)
        self.logger.addHandler(sh)
        self.stream = sh.stream
        # 防止在终端重复打印
        self.logger.propagate = 0

        # output to user define file
        if filename is not None:
            fh = logging.FileHandler(filename, 'a')
            fh.setFormatter(formatter)
            fh.setLevel(logging.DEBUG)
            self.logger.addHandler(fh)
            self.logger.propagate = 0

    @color_text_decorator
    def hint(self, string):
        # 去除多余连续空格
        strTmp = str(string)
        strTmp = ' '.join(strTmp.split())
        main_logger.hint("[" + self.name + "] " + strTmp)
        if self.LOG_LEVEL >= 5:
            return self.logger.debug(strTmp)
        else:
            pass

    @color_text_decorator
    def debug(self, string):
        # 去除多余连续空格
        strTmp = str(string)
        strTmp = ' '.join(strTmp.split())
        main_logger.debug("[" + self.name + "] " + strTmp)
        if self.LOG_LEVEL >= 4:
            return self.logger.debug(strTmp)
        else:
            pass

    @color_text_decorator
    def info(self, string):
        # 去除多余连续空格
        strTmp = str(string)
        strTmp = ' '.join(strTmp.split())
        main_logger.info("[" + self.name + "] " + strTmp)
        if self.LOG_LEVEL >= 3:
            return self.logger.info(strTmp)
        else:
            pass

    @color_text_decorator
    def warn(self, string):
        # 去除多余连续空格
        strTmp = str(string)
        strTmp = ' '.join(strTmp.split())
        main_logger.warn("[" + self.name + "] " + strTmp)
        if self.LOG_LEVEL >= 2:
            return self.logger.warning(strTmp)
        else:
            pass

    @color_text_decorator
    def error(self, string):
        # 去除多余连续空格
        strTmp = str(string)
        strTmp = ' '.join(strTmp.split())
        main_logger.error("[" + self.name + "] " + strTmp)
        if self.LOG_LEVEL >= 1:
            return self.logger.error(strTmp)
        else:
            pass


class TestLogModule(object):

    def __init__(self):
        pass

    def runtest(self):
        logger = Logger('TEST')

        iCount = 10
        while True:
            iCount = iCount + 1
            logger.error(str(iCount))

            logger.hint('hint   22   333   4444     55555      666666')
            logger.debug('debug   22   333   4444     55555      666666')
            logger.info('info  22   333   4444     55555      666666')
            logger.warn('warn   22   333   4444     55555      666666')
            logger.error('error   22   333   4444     55555      666666')

            logger.hint('hint   22   333   4444 我们 55555      666666')
            logger.debug('debug  22   333   4444 我们 55555      666666')
            logger.info('info   22   333   4444 我们 55555      666666')
            logger.warn('warn  22   333   4444 我们 55555      666666')
            logger.error('error  22   333   4444 我们 55555      666666')

            logger.hint(u'hint  22   333   4444  中国   55555      666666')
            logger.debug(u'debug 22   333   4444  中国    55555      666666')
            logger.info(u'info  22   333   4444   中国   55555      666666')
            logger.warn(u'warn   22   333   4444    中国  55555      666666')
            logger.error(u'error   22   333   4444   中国  55555      666666')

            time.sleep(1)
            if iCount >= 10:
                break

if __name__ == '__main__':
    TestLogModule().runtest()
