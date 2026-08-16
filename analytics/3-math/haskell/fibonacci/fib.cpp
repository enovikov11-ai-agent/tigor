#include <boost/multiprecision/cpp_int.hpp>
#include <iostream>

int main() {

  int n;
  boost::multiprecision::cpp_int a = 1, b = 1;

  std::cin >> n;

  if (n <= 2) {
    std::cout << 1;
    return 0;
  }

  n -= 2;

  for (; n >= 2; n -= 2) {
    a += b;
    b += a;
  }

  if (n == 0) {
    std::cout << b;
  } else {
    a += b;
    std::cout << a;
  }

  return 0;
}