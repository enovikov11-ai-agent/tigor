#include <cublas_v2.h>
#include <cuda_runtime.h>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <unistd.h>
#include <time.h>

#define CK(x) do { cudaError_t e=(x); if(e!=cudaSuccess){ \
  fprintf(stderr,"CUDA %s:%d: %s\n",__FILE__,__LINE__,cudaGetErrorString(e)); exit(1);} } while(0)

#define CB(x) do { cublasStatus_t s=(x); if(s!=CUBLAS_STATUS_SUCCESS){ \
  fprintf(stderr,"CUBLAS %s:%d: %d\n",__FILE__,__LINE__,(int)s); exit(1);} } while(0)

__global__ void mem_sweep(float *a, float *b, float *c, float *d, size_t n) {
  size_t i = blockIdx.x * blockDim.x + threadIdx.x;
  size_t stride = blockDim.x * gridDim.x;
  for (size_t x = i; x < n; x += stride) {
    float av = a[x];
    float bv = b[x];
    float cv = c[x];
    float r = fmaf(av, 1.0001000f, bv) - cv * 0.9999000f;
    d[x] = r;
    a[x] = r + 0.000001f;
  }
}

__global__ void fma_spin(float *a, size_t n, int iters) {
  size_t i = blockIdx.x * blockDim.x + threadIdx.x;
  size_t stride = blockDim.x * gridDim.x;
  for (size_t x = i; x < n; x += stride) {
    float v = a[x] + (float)(x & 255) * 0.001f;
    for (int k = 0; k < iters; k++) {
      v = fmaf(v, 1.000000119f, 0.000000013f);
      v = fmaf(v, 0.999999881f, 0.000000017f);
      v = fmaf(v, 1.000000238f, 0.000000019f);
      v = fmaf(v, 0.999999762f, 0.000000023f);
    }
    a[x] = v;
  }
}

static double now_sec() {
  timespec ts;
  clock_gettime(CLOCK_MONOTONIC, &ts);
  return ts.tv_sec + ts.tv_nsec * 1e-9;
}

int main(int argc, char **argv) {
  int N = argc > 1 ? atoi(argv[1]) : 49152;
  int cycles = argc > 2 ? atoi(argv[2]) : 0;
  int gemm_iters = argc > 3 ? atoi(argv[3]) : 6;
  int mem_iters = argc > 4 ? atoi(argv[4]) : 3;
  int idle_ms = argc > 5 ? atoi(argv[5]) : 150;
  int spin_iters = argc > 6 ? atoi(argv[6]) : 5000;

  size_t elems = (size_t)N * (size_t)N;
  size_t bytes = elems * sizeof(float);

  printf("N=%d elems=%zu bytes_per_matrix=%.2f GiB total_alloc=%.2f GiB cycles=%d gemm=%d mem=%d idle_ms=%d spin_iters=%d\n",
         N, elems, bytes / 1073741824.0, bytes * 4.0 / 1073741824.0,
         cycles, gemm_iters, mem_iters, idle_ms, spin_iters);
  fflush(stdout);

  float *A, *B, *C, *D;
  CK(cudaMalloc(&A, bytes));
  CK(cudaMalloc(&B, bytes));
  CK(cudaMalloc(&C, bytes));
  CK(cudaMalloc(&D, bytes));

  CK(cudaMemset(A, 0x3f, bytes));
  CK(cudaMemset(B, 0x27, bytes));
  CK(cudaMemset(C, 0x11, bytes));
  CK(cudaMemset(D, 0x00, bytes));

  cublasHandle_t h;
  CB(cublasCreate(&h));
#if CUBLAS_VERSION >= 11000
  CB(cublasSetMathMode(h, CUBLAS_TF32_TENSOR_OP_MATH));
#endif

  const float alpha = 1.0f;
  const float beta = 0.0f;

  int block = 256;
  int grid_mem = 262144;
  int grid_spin = 65535;
  size_t spin_elems = elems < (size_t)134217728 ? elems : (size_t)134217728;

  for (int cycle = 1; cycles == 0 || cycle <= cycles; cycle++) {
    double t0 = now_sec();
    printf("cycle %d start\n", cycle);
    fflush(stdout);

    printf("cycle %d gemm\n", cycle);
    fflush(stdout);
    for (int i = 0; i < gemm_iters; i++) {
      CB(cublasSgemm(h, CUBLAS_OP_N, CUBLAS_OP_N,
                     N, N, N,
                     &alpha,
                     A, N,
                     B, N,
                     &beta,
                     C, N));
    }
    CK(cudaDeviceSynchronize());

    printf("cycle %d mem\n", cycle);
    fflush(stdout);
    for (int i = 0; i < mem_iters; i++) {
      mem_sweep<<<grid_mem, block>>>(A, B, C, D, elems);
      CK(cudaGetLastError());
      CK(cudaMemcpyAsync(B, D, bytes, cudaMemcpyDeviceToDevice));
      CK(cudaMemcpyAsync(D, C, bytes, cudaMemcpyDeviceToDevice));
      CK(cudaDeviceSynchronize());
    }

    printf("cycle %d spin\n", cycle);
    fflush(stdout);
    fma_spin<<<grid_spin, block>>>(A, spin_elems, spin_iters);
    CK(cudaGetLastError());
    CK(cudaDeviceSynchronize());

    double t1 = now_sec();
    printf("cycle %d done active_sec=%.3f idle_ms=%d\n", cycle, t1 - t0, idle_ms);
    fflush(stdout);

    if (idle_ms > 0) usleep((useconds_t)idle_ms * 1000);
  }

  CB(cublasDestroy(h));
  CK(cudaFree(A));
  CK(cudaFree(B));
  CK(cudaFree(C));
  CK(cudaFree(D));
  return 0;
}
