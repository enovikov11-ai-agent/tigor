root@045d487df931:~# vim fibonacci.asm
root@045d487df931:~# nasm -f elf64 fibonacci.asm
root@045d487df931:~# gcc -no-pie -o fibonacci fibonacci.o
/usr/bin/ld: warning: fibonacci.o: missing .note.GNU-stack section implies executable stack
/usr/bin/ld: NOTE: This behaviour is deprecated and will be removed in a future version of the linker

root@045d487df931:~# ./fibonacci 
F(0) = 0

root@045d487df931:~# ./fibonacci 
F(-1493930559) = 0
F(-1493930559) = 0
F(-1493930559) = 0
...

root@045d487df931:~# ./fibonacci 
F(0) = 0

root@045d487df931:~# ./fibonacci 
F(-1716807199) = 0
...

root@045d487df931:~# ./fibonacci 
F(-594875183) = 0
...