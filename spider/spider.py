# encoding=utf8
# author:shellvon
# See :https://github.com/shellvon/CodeFragment/blob/master/spider/douban.py

import threading
import Queue
import md5      # for hash...
import time     # for test time.


class ThreadingPool(object):
    """docstring for threadingPool"""
    def __init__(self, thread_num):
        self.threads = []
        self.work_queue = Queue.Queue()
        self.failed_num = 0
        self.success_num = 0
        self.jobs = []
        self.thread_num = thread_num
        self.thread_name = threading.current_thread().getName()
        self._init_pool()
        self.running_num = 0

    def _init_pool(self):
        """
        init the thread pool
        """
        # add all the downloadImageThread
        for i in xrange(self.thread_num):
            self.threads.append(DownloadImageThread(self))
        # add the progress thread.
        self.threads.append(ProgressInfoThread(self))

    def add_job(self, func, identify, args):
        """
        add the job to the pool
        """
        if identify not in self.jobs:
            self.jobs.append(identify)
            self.work_queue.put((func, args))

    def get_job(self):
        """
        get the job
        """
        return self.work_queue.get(block=False)

    def job_done(self):
        self.work_queue.task_done()

    def get_success_num(self):
        return self.success_num

    def get_failed_num(self):
        return self.failed_num

    def increase_success_num(self):
        self.success_num += 1

    def increase_failed_num(self):
        self.failed_num += 1

    def increase_running_num(self):
        self.running_num += 1

    def decrease_running_num(self):
        self.running_num -= 1

    def get_running_num(self):
        return self.running_num

    def start_job(self):
        for job in self.threads:
            job.start()

    def wait(self):
        """
        wait all jobs to completed
        """
        for job in self.threads:
            if job.isAlive():
                job.join()

    def _hash(self, source):
        """
        hash the jobs to identify
        """
        return md5.md5(source).hexdigest()

    def get_progressinfo(self):
        info = {
            'job_number': len(self.jobs),
            'success': self.success_num,
            'failed': self.failed_num,
            'thread_num': self.thread_num,
            'running_num': self.running_num,
        }
        return info

    def get_thread_name(self):
        return self.thread_name


class ProgressInfoThread(threading.Thread):
    """for the spider to display the progress info """
    def __init__(self, pool, time_to_sleep=10.0):
        self.time_to_sleep = time_to_sleep
        self.thread_pool = pool
        threading.Thread.__init__(self)

    def run(self):
        while True:
            running_now = self.thread_pool.get_running_num()    # add this for break out loop
            if running_now <= 0:
                break
            progess_info = self.thread_pool.get_progressinfo()
            print progess_info
            time.sleep(self.time_to_sleep)


class DownloadImageThread(threading.Thread):
    """
    for download the image
    """
    def __init__(self, pool):
        threading.Thread.__init__(self)
        self.thread_pool = pool

    def run(self):
        while True:
            try:
                func, args = self.thread_pool.get_job()
                self.thread_pool.increase_running_num()
                result = func('url', args)
                if result:
                    self.thread_pool.increase_success_num()
                    if args.limit and self.thread_pool.get_success_num() >= args.limit:
                        break
                else:
                    self.thread_pool.increase_failed_num()
                self.thread_pool.decrease_running_num()
                self.thread_pool.job_done()
            except Queue.Empty:
                # pass
                break
            except Exception, e:
                print str(e)
                break