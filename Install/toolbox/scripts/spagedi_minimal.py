#!/usr/bin/env python
import sys, traceback, Queue, threading, subprocess
from pprint import pprint as pp

def threadframe():
    print >> sys.stderr, "\n*** STACKTRACE - START ***\n"
    code = []
    for threadId, stack in sys._current_frames().items():
        code.append("\n# ThreadID: %s" % threadId)
        for filename, lineno, name, line in traceback.extract_stack(stack):
            code.append('File: "%s", line %d, in %s' % (filename,
                                                        lineno, name))
            if line:
                code.append("  %s" % (line.strip()))
    for line in code:
        print >> sys.stderr, line
    print >> sys.stderr, "\n*** STACKTRACE - END ***\n"

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
    output_thread = threading.Thread(target=enqueue_output, args=(p.stdout, out_queue))
    # output_thread.daemon = True
    output_thread.start()
    for command in sequence:
        p.stdin.write(command)
        import pdb; pdb.set_trace()
        output = get_output(out_queue)
        # print output

if __name__ == '__main__':
    main()
