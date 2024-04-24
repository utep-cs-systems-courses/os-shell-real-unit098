#! /usr/bin/env python3

import os, sys, re, os.path


fdOut = os.open("p0-output.txt", os.O_CREAT | os.O_WRONLY)
fdIn = 0

print(f"fdIn={fdIn}, fdOut={fdOut}", file=sys.stderr)

# note that
#  fd #0 is "standard input" (by default, attached to kbd)
#  fd #1 is "standard ouput" (by default, attached to display)
#  fd #2 is "standard error" (by default, attached to display for error output)

prompt = os.getenv('PS1', "$ ")
lineNum = 1
def handlekid(bcmd, line, pipe=False, r=1, w=1, so=1):
    vtd = ['&']
    if pipe:
        os.close(0)
        os.dup(r)
        os.close(r)
        os.close(w)
        os.set_inheritable(0, True)
    args=[i.decode() for i in bcmd]
    for i in range(len(args)):
        if args[i] == '|':
            r,w = os.pipe()
            os.set_inheritable(r, True)
            os.set_inheritable(w, True)
            f = os.fork()
            if f<0:
                print("something has gon terribly bad :<", file=sys.stderr)
            if f==0:
                os.set_inheritable(1, True)
                handlekid(bcmd[i+1::], bcmd[i+1], True, r=r, w=w)
            
            else:
                print("I am a father", file=sys.stderr)
                args=args[:i:]
                os.close(1)
                os.dup(w)
                os.close(w)
                os.close(r)
                os.set_inheritable(1, True)
            break
        if args[i] == '>':
            os.close(1)
            fd = os.open(args[i+1], os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
            os.set_inheritable(1, True)
            print(fd, file = sys.stderr)
            vtd.append(args[i])
            vtd.append(args[i+1])
        if args[i] == '<':
            os.close(0)
            os.open(args[i+1], os.O_RDONLY)
            os.set_inheritable(0, True)
            vtd.append(args[i])
            vtd.append(args[i+1])
        
            
    args = [i for i in args if i not in vtd]        
    print(args, file=sys.stderr)
    if b'/' in line:
        try:
            os.execve(os.path.abspath(line.decode()), args, os.environ)
        except FileNotFoundError:
            pass
    for i in re.split(':', os.environ['PATH']):
        try:
            os.execve(i+'/'+line.decode(), args, os.environ)
        except FileNotFoundError:
            pass
    os.write(2, f"{line.decode()}File not found\n".encode())
    sys.exit(0)

while 1:
    os.write(1, prompt.encode())
    input = os.read(fdIn, 10000)  # read up to 10k bytes
    if len(input) == 0: break     # done if nothing read
    lines = re.split(b"\n", input)
    lines = [i for i in lines if i != b'']
    print(lines, file=sys.stderr)
    for cmd in lines:
        bcmd = re.split(b" ", cmd)
        bcmd = [i for i in bcmd if i !=b'']
        line = bcmd[0]
        if line == "exit".encode():
            print("shell is ded", file=sys.stderr)
            sys.exit(0)
        if line == "cd".encode():
            if len(bcmd) != 2:
                print("wrong amount of args", file=sys.stderr)
            elif (not os.path.isdir(os.path.abspath(bcmd[1].decode()))):
                print("path does not exist", file=sys.stderr)
            else:
                os.environ['OLDPWD'] = os.environ['PWD']
                os.environ['PWD'] = os.path.abspath(bcmd[1].decode())
                os.chdir(os.path.abspath(bcmd[1].decode()))
                print(os.environ['PWD']+' old '+os.environ['OLDPWD'], file=sys.stderr)
        else:
            f=os.fork()
            if f<0:
                print("something has gon terribly bad :<", file=sys.stderr)
            if f==0:
                handlekid(bcmd, line)
            else:
                print("I am a father", file=sys.stderr)
                if(b'&' not in bcmd):
                    pid, ec = os.waitpid(f, 0)
                    print(f"my kid dieded his name was {pid} and his cod was {ec}", file=sys.stderr)
                
    
            
        
