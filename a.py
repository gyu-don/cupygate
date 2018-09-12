import time
from circuit import Circuit as GpuCircuit
from blueqat import Circuit as CpuCircuit

print("Benchmark of Circuit(n).h[:].run()")
print("qubits\tCPU (ms)\tGPU (ms)")
for n in [1, 3, 5, 10, 13, 15, 17, 19, 20, 22, 23, 24]:
    start = time.time()
    CpuCircuit(n).h[:].run()
    cpu_time = time.time() - start
    start = time.time()
    GpuCircuit(n).h[:].run()
    gpu_time = time.time() - start
    print(n, cpu_time * 1000, gpu_time * 1000, sep="\t")
