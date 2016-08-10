import os
import os.path
import time
from dispatcher import dispatch_files
def directory_files(directory):
    '''Return a list of full paths of files in DIRECTORY.'''
    results=[]
    for root,dirs,files in os.walk(directory):
        full_paths=[os.path.join(root,f) for f in files]
        results.extend(full_paths)
    return results

def directory_files_and_size(directory):
    '''Return a list of full paths and sizes of files in DIRECTORY.'''
    files = directory_files(directory)
    files_and_sizes = set([(f,os.path.getsize(f)) for f in files])
    return files_and_sizes

def directory_files_until_nochange(directory,interval=5):
    old = directory_files_and_size(directory)
    time.sleep(interval)
    new = directory_files_and_size(directory)
    while old != new:
        old,new = new,directory_files_and_size(directory)
    return [file_and_size[0] for file_and_size in new]

if __name__ == "__main__":
    directory=sys.argv[1]
    while True:
        old = directory_files(directory)
        new = directory_files_until_nochange(directory)
        diff = new - old
        dispatcher_files(diff)
        sleep(60)
