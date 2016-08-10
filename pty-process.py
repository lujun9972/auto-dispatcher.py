#!python3
import pty
import sys

pty.spawn(sys.argv[1:])

# import os
# import termios

# def master_read(fd):
#     print(fd)
#     data = os.read(fd,1024)
#     print("main",data)
#     return data

# def stdin_read(fd):
#     print(fd)
#     data = os.read(fd,1024)
#     print("stdin",data)
#     return data

# pty.spawn(sys.argv[1:],master_read,stdin_read)

# pid,fd = pty.fork()
# if pid == 0:
#     command = " ".join(sys.argv[1:])
#     os.execlp("bash","-c",command)
# else:
#     old = termios.tcgetattr(fd)
#     new = termios.tcgetattr(fd)
#     new[3] = new[3] & ~termios.ECHO          # lflags
#     termios.tcsetattr(fd, termios.TCSADRAIN, new)
#     os.write(fd,sys.stdin.readline().encode())
#     os.wait()
#     print(os.read(fd,1024).decode())
