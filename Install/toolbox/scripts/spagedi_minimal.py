#!/usr/bin/env python
import Queue
import threading
import subprocess

def enqueue_output(out, queue):
    for line in iter(out.readline, b''):
        queue.put(line)
    out.close()

def get_output(out_queue):
    output = ''
    try:
        while True:
            output += out_queue.get_nowait()
    except Queue.Empty:
        return output

def main():
    spagedi_file_path = r'C:\Users\Sparky\AppData\Roaming\geneGIS\spagedi_data.txt'
    results = r'C:\Users\Sparky\src\genegis\tests\data\test_spagedi_export.txt'
    spagedi_executable_path = r'C:\Users\Sparky\src\genegis\Install\toolbox\lib\SPAGeDi-1.4.exe'
    sequence = [spagedi_file_path, results] + list(' 214    ')
    p = subprocess.Popen([spagedi_executable_path], stdin=subprocess.PIPE,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         shell=False, universal_newlines=True)
    out_queue = Queue.Queue()
    outThread = threading.Thread(target=enqueue_output, args=(p.stdout, out_queue))
    outThread.daemon = True
    outThread.start()
    for command in sequence:
        p.stdin.write(command)
        output = get_output(out_queue)
        print output

if __name__ == '__main__':
    main()