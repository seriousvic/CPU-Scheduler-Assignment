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

    """
    This function updates the mode of the process to 'ready'.
    """

    def descheduleFromCPU(self):
        assert (self.mode == 'burst')
        self.mode = 'ready'


class RRQueue:
    """
    This class implements the RR Queue for MLFQ scheduler.
    isActive is a boolean variable that indicates whether the queue is active or not.
    Being active means that some process from the queue is currently running on the CPU.
    If isActive is False, then the queue is not active and the currentRunning process is None.
    Otherwise, the currentRunning process is the process that is currently running on the CPU.
    """

    def __init__(self, queue, quantum, isActive):
        self.quantum = quantum
        self.queue = queue
        self.time = 0  # time elapsed on the current burst
        self.idx = 0
        self.isActive = isActive
        self.lastRemoved = None
        self.currentRunning = self.queue[0].id if len(self.queue) > 0 and self.isActive else None

    """
    This function goes over the queue in a round-robin fashion and
    finds the next process that is ready. If no such process exists,
    isActive is set to False and currentRunning is set to None.
    If a process is found, isActive is set to True and currentRunning
    is set to the id of the process.
    """

    def nextReadyProcess(self):
        if not self.isActive:
            return
        cnt = 0
        assert (len(self.queue) > 0)
        while self.queue[self.idx].mode != 'ready':
            self.idx = (self.idx + 1) % len(self.queue)
            cnt += 1
            if cnt == len(self.queue):  # all processes are waiting
                self.isActive = False
                self.currentRunning = None
                return

        self.isActive = True
        self.currentRunning = self.queue[self.idx].id

    """
    This function is called when the process currently running on the CPU
    finishes its burst and starts waiting for IO. It calls nextReadyProcess function
    to find the next ready process and update internal state.
    """

    def processIO(self, id):
        assert (self.currentRunning == id)
        self.time = 0
        self.nextReadyProcess()

    """
    This function is called when the process currently running on the CPU
    finishes completely. It deletes the process from its queue and calls
    nextReadyProcess function to find the next ready process
    """

    def processDone(self, id):
        assert (self.currentRunning == id)
        self.time = 0
        self.queue = self.queue[:self.idx] + self.queue[self.idx + 1:]
        if self.idx == len(self.queue):
            self.idx = 0

        if len(self.queue) == 0:
            self.isActive = False
            self.currentRunning = None
        self.nextReadyProcess()

    """
    Function to make the current queue inactive (for example some higher priority queue became active)
    """

    def makeInactive(self):
        self.currentRunning = None
        self.isActive = False

    """
    Function to make current queue active (if possible).
    Returns True on success and False otherwise.
    """

    def makeActive(self):
        if len(self.queue) == 0:
            return False
        if self.isActive:
            return True
        self.isActive = True
        self.nextReadyProcess()
        return self.isActive

    """
    Add a new process to the current queue.
    """

    def addProcess(self, proc):
        self.queue.append(proc)

    """
    This simulates one time unit for the current queue. If the quantum is expired,
    the process is descheduled from the CPU, removed from the current queue and the next ready process is scheduled.
    It also sets lastRemoved to the id of the process that was removed from the queue
    (so that the scheduler can add it to the next queue).

    Returns False if quatum expires, and True otherwise.
    """

    def simulate(self):
        if not self.isActive:
            return True
        self.time += 1
        if self.time == self.quantum:  # quantum expired
            self.time = 0
            self.lastRemoved = self.queue[self.idx].id
            # Removing the process from the queue
            self.queue = self.queue[:self.idx] + self.queue[self.idx + 1:]
            if self.idx == len(self.queue):
                self.idx = 0

            # If all processes have been removed, make the queue inactive
            if len(self.queue) == 0:
                self.isActive = False
                self.currentRunning = None
            self.nextReadyProcess()
            return False
        return True

    def getCurrentRunningProcess(self):
        return self.currentRunning

    def getLastRemoved(self):
        return self.lastRemoved


class MLFQScheduler:
    """
    MLFQ scheduler maintains three queues of processes - first two work in round-robin fashion
    and the last is a FCFS queue.
    """

    def __init__(self, processes):
        assert (len(processes) > 0)
        self.processes = processes
        self.n = len(processes)
        self.rr_queues = [RRQueue(processes, 5, True), RRQueue([], 10, False)]
        self.fcfs_queue = Queue()
        self.priorities = [0] * self.n  # priorities of processes (0 -> highest, 2 -> lowest)
        self.cpu = processes[0].id
        self.processes[self.cpu].scheduleOnCPU()
        self.total_time = 0
        self.cpu_time = 0
        self.done = 0  # No of processes done

    """
    Called by a process when it is ready to run on CPU. 
    """

    def processReady(self, id):
        if self.priorities[id] == 2:
            self.fcfs_queue.put(id)
        # If the priority is 0 or 1, then the process is already in the RR queue

    """
    Called by a running process when it is finished. 
    """

    def processDone(self, id):
        assert (self.cpu == id)
        self.done += 1
        self.cpu = None

        # Call processDone on the RR queue
        if self.priorities[id] < 2:
            self.rr_queues[self.priorities[id]].processDone(id)

    """
    Called by a running process when it needs to wait for IO.
    """

    def processIO(self, id):
        assert (self.cpu == id)
        self.cpu = None

        # Call processIO on the RR queue
        if self.priorities[id] < 2:
            self.rr_queues[self.priorities[id]].processIO(id)

    """
    Simulates the scheduler for a single time unit.
    Updates the total time and CPU time.
    Returns True if all processes are done, and False otherwise.
    """

    def simulate(self):
        if self.done == self.n:
            return True

        # If the CPU is free or running process is not of highest priority,
        # try to schedule a process from the highest priority queue
        if self.cpu == None or self.priorities[self.cpu] > 0:
            if self.rr_queues[0].makeActive():  # If the queue becomes active
                if self.cpu is not None:  # If the CPU was running a process, deschedule it
                    self.processes[self.cpu].descheduleFromCPU()
                    if self.priorities[self.cpu] == 1:
                        self.rr_queues[1].makeInactive()
                    else:
                        self.fcfs_queue.put(self.cpu)

                # Schedule the process from the queue on the CPU
                self.cpu = self.rr_queues[0].getCurrentRunningProcess()
                self.processes[self.cpu].scheduleOnCPU()

        # If the CPU is free or running process is not of second highest priority,
        # try to schedule a process from the second highest priority queue
        if self.cpu == None or self.priorities[self.cpu] > 1:
            if self.rr_queues[1].makeActive():
                if self.cpu is not None:
                    self.processes[self.cpu].descheduleFromCPU()
                    self.fcfs_queue.put(self.cpu)
                self.cpu = self.rr_queues[1].getCurrentRunningProcess()
                self.processes[self.cpu].scheduleOnCPU()

        # If the CPU is still free, try to schedule a process from the lowest priority queue
        if self.cpu == None:
            if not self.fcfs_queue.empty():
                self.cpu = self.fcfs_queue.get()
                self.processes[self.cpu].scheduleOnCPU()

        if self.cpu != None:
            self.cpu_time += 1

        self.total_time += 1

        for p in self.processes:
            p.simulate()

        # Simulate the RR queues
        if not self.rr_queues[0].simulate():
            # If the quantum expired, move the process to the next queue and deschedule it
            removed = self.rr_queues[0].getLastRemoved()
            self.priorities[removed] += 1
            self.rr_queues[1].addProcess(self.processes[removed])
            self.processes[removed].descheduleFromCPU()
            self.cpu = None

        if not self.rr_queues[1].simulate():
            # If the quantum expired, move the process to the next queue and deschedule it
            removed = self.rr_queues[1].getLastRemoved()
            self.priorities[removed] += 1
            self.fcfs_queue.put(removed)
            self.processes[removed].descheduleFromCPU()
            self.cpu = None

        return self.done == self.n

    """
    This function prints the stats of the scheduler.
    """

    def printStats(self):
        print("Scheduler: MLFQ")
        print("CPU Utilization: %.2f%%" % (self.cpu_time / self.total_time * 100.0))

        print("\tTw\tTtr\tTr")
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

    scheduler = MLFQScheduler(processes)
    for p in processes:
        p.scheduler = scheduler

    while not scheduler.simulate():
        pass

    scheduler.printStats()


if __name__ == '__main__':
    main()
