; fibonacci.asm — выводит F(0)…F(9)
; сборка:  nasm -f elf64 fibonacci.asm
; линковка: gcc -no-pie -o fibonacci fibonacci.o

        global  main
        extern  printf

section .note.GNU-stack noalloc noexec nowrite

;----------------------------------------------------------
section .data
fmt     db  "F(%d) = %llu", 10, 0     ; формат строки: "F(n) = value\n"

;----------------------------------------------------------
section .text
; SysV-AMD64 ABI:
;   RDI, RSI, RDX, RCX, R8, R9 — первые 6 целочисленных аргументов
;   RAX = 0 перед variadic printf
;   RDI/RSI/RDX/RCX/R8/R9/R10/R11 — caller-saved, значит
;   мы обязаны сами сохранять их, если ценим их содержимое.

main:
        push    rbp
        mov     rbp, rsp
        sub     rsp, 16              ; выровняли стек (RSP % 16 == 0)

        mov     ecx, 10              ; сколько чисел печатать
        xor     edi, edi             ; n = 0
        xor     r8,  r8              ; F(n-2) = 0
        mov     r9,  1               ; F(n-1) = 1

.loop:
        cmp     edi, ecx             ; n >= 10?
        jge     .done

        ; —— печать текущего Fibonacci ——
        push    r8                   ; F(n-2)
        push    r9                   ; F(n-1)
        push    rdi                  ; n
        push    rcx                  ; счётчик
        sub     rsp, 8               ; довели объём до 40 байт ⇒ RSP % 16 == 8

        mov     esi, edi             ; 2-й аргумент -> %d   (n)
        mov     rdx, r8              ; 3-й аргумент -> %llu (F(n))
        lea     rdi, [rel fmt]       ; 1-й аргумент -> адрес строки
        xor     eax, eax             ; printf требует RAX = 0
        call    printf

        add     rsp, 8               ; вернули выравнивание
        pop     rcx                  ; восстановили счётчик
        pop     rdi                  ; восстановили n
        pop     r9                   ; восстановили F(n-1)
        pop     r8                   ; восстановили F(n-2)

        ; —— вычисление следующего Fibonacci ——
        mov     rax, r8              ; rax = F(n)
        add     rax, r9              ; rax = F(n) + F(n-1)
        mov     r8,  r9              ; F(n-2) = старое F(n-1)
        mov     r9,  rax             ; F(n-1) = новое значение
        inc     edi                  ; n++

        jmp     .loop

.done:
        xor     eax, eax             ; код возврата 0
        add     rsp, 16
        pop     rbp
        ret
