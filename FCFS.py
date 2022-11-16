from queue import Queue


class Process:
    """
    Each Process has a list of burst times, and a list of I/O times.
    idx_burst and idx_io are the indices of the current burst and I/O time in the lists
    waiting_time is the total time the process has spent waiting
    turnaround_time is the total time the process has spent running
    response_time is the time the process first started running
    mode is one of 'ready', 'burst', 'io', or 'done':
        - 'ready' means the process is waiting to be scheduled on the CPU
        - 'burst' means the process is currently running on the CPU
        - 'io' means the process is currently waiting for I/O
        - 'done' means the process has finished running
    """

    def __init__(self, id, times, sched):
        self.id = id
        self.n = len(times)
        self.burst_times = times[::2]
        self.io_times = times[1::2]
        self.mode = 'ready'
        self.scheduler = sched
        self.idx_burst = 0
        self.idx_io = 0

        self.waiting_time = 0
        self.turnaround_time = 0
        self.response_time = None

    """
    This function simulates the process running on the CPU for a single time unit.
    It returns True if the process is done running, and False otherwise.
    """

    def simulate(self):
        if self.mode == 'done':
            return True

        self.turnaround_time += 1
        if self.mode == 'burst':
            self.burst_times[self.idx_burst] -= 1
            if self.burst_times[self.idx_burst] == 0:
                self.mode = 'io'
                self.idx_burst += 1
                if self.idx_burst == self.n // 2 + 1:
                    self.mode = 'done'
                    self.scheduler.processDone(self.id)
                    return True
                else:
                    self.scheduler.processIO(self.id)

        elif self.mode == 'io':
            self.io_times[self.idx_io] -= 1
            if self.io_times[self.idx_io] == 0:
                self.mode = 'ready'
                self.idx_io += 1
                self.scheduler.processReady(self.id)
        elif self.mode == 'ready':
            self.waiting_time += 1

        return False

    """
    This function updates the mode of the process to 'ready'.
    """

    def scheduleOnCPU(self):
        assert (self.mode == 'ready')
        self.mode = 'burst'
        if self.response_time == None:
            self.response_time = self.turnaround_time


class FCFSScheduler:
    """
    FCFS scheduler maintains a queue of processes that are ready to run.
    """

    def __init__(self, processes):
        assert (len(processes) > 0)
        self.processes = processes
        self.cpu = processes[0].id  # id of the process currently running on the CPU
        processes[0].scheduleOnCPU()
        self.queue = Queue()
        for i in range(1, len(processes)):
            self.queue.put(i)
        self.total_time = 0
        self.cpu_time = 0
        self.done = 0  # No of processes done
        self.n = len(processes)

    """
    Called by a process when it is ready to run on CPU. 
    Puts the process into the queue.
    """

    def processReady(self, id):
        self.queue.put(id)

    """
    Called by a running process when it is done running. 
    """

    def processDone(self, id):
        assert (self.cpu == id)
        self.done += 1
        self.cpu = None

    """
    Called by a running process when it needs to wait for IO.
    """

    def processIO(self, id):
        assert (self.cpu == id)
        self.cpu = None

    """
    Simulates the scheduler for a single time unit.
    If the CPU is idle, it schedules the next process in the queue.
    Updates the total time and CPU time.
    Returns True if all processes are done, and False otherwise.
    """

    def simulate(self):
        if self.done == self.n:
            return True
        if self.cpu == None:
            if not self.queue.empty():
                self.cpu = self.queue.get()
                self.processes[self.cpu].scheduleOnCPU()
        if self.cpu != None:
            self.cpu_time += 1

        self.total_time += 1

        for p in self.processes:
            p.simulate()

        return self.done == self.n

    """
    This function prints the stats of the scheduler.
    """

    def printStats(self):
        print("Scheduler: FCFS")
        print("CPU Utilization: %.2f%%" % (self.cpu_time / self.total_time * 100.0))

        print("Proc\tTw\tTt\tTr")
        for p in self.processes:
            print(f"P{p.id + 1}\t{p.waiting_time}\t{p.turnaround_time}\t{p.response_time}")

        waiting_times = [p.waiting_time for p in self.processes]
        turnaround_times = [p.turnaround_time for p in self.processes]
        response_times = [p.response_time for p in self.processes]
        print(
            f"Avg\t{sum(waiting_times) / self.n:.2f}\t{sum(turnaround_times) / self.n:.2f}\t{sum(response_times) / self.n:.2f}")


def main():
    process_times = [
        [5, 27, 3, 31, 5, 43, 4, 18, 6, 22, 4, 26, 3, 24, 4],
        [4, 48, 5, 44, 7, 42, 12, 37, 9, 76, 4, 41, 9, 31, 7, 43, 8],
        [8, 33, 12, 41, 18, 65, 14, 21, 4, 61, 15, 18, 14, 26, 5, 31, 6],
        [3, 35, 4, 41, 5, 45, 3, 51, 4, 61, 5, 54, 6, 82, 5, 77, 3],
        [16, 24, 17, 21, 5, 36, 16, 26, 7, 31, 13, 28, 11, 21, 6, 13, 3, 11, 4],
        [11, 22, 4, 8, 5, 10, 6, 12, 7, 14, 9, 18, 12, 24, 15, 30, 8],
        [14, 46, 17, 41, 11, 42, 15, 21, 4, 32, 7, 19, 16, 33, 10],
        [4, 14, 5, 33, 6, 51, 14, 73, 16, 87, 6]
    ]
    n = len(process_times)
    processes = [Process(i, process_times[i], None) for i in range(n)]

    scheduler = FCFSScheduler(processes)
    for p in processes:
        p.scheduler = scheduler

    while not scheduler.simulate():
        pass

    scheduler.printStats()


if __name__ == '__main__':
    main()
