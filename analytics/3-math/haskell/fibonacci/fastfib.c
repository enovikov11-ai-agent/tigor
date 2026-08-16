#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STACK_BIGINT_SIZE 1000000

void add(char *to, char *from, int *size) {
  char acc = 0;

  for (size_t i = 0; i < *size; i++) {
    to[i] += from[i] + acc;
    acc = to[i] / 10;
    to[i] %= 10;
  }

  if (acc > 0) {
    if (*size >= STACK_BIGINT_SIZE)
      exit(1);

    to[*size] = acc;
    *size += 1;
  }
}

void print(char *num, int *size) {
  int i = *size - 1;

  for (; i > 0 && num[i] == 0; i--) {
  }

  for (; i >= 0; i--) {
    putc('0' + num[i], stdout);
  }

  putc('\n', stdout);
}

int main() {
  int n;
  scanf("%d", &n);

  if (n <= 2) {
    printf("%d\n", 1);
    return 0;
  }

  n -= 2;

  char a[STACK_BIGINT_SIZE], b[STACK_BIGINT_SIZE];
  int size = 1;

  memset(a, 0, sizeof(a));
  memset(b, 0, sizeof(b));

  a[0] = 1;
  b[0] = 1;

  for (; n >= 2; n -= 2) {
    add(a, b, &size);
    add(b, a, &size);
  }

  if (n == 0) {
    print(b, &size);
  } else {
    add(a, b, &size);
    print(a, &size);
  }

  return 0;
}