import matplotlib.pyplot as plt
import numpy as np

file = open("REvsPI.dat", 'r')
outFile = open("REvsPI_ALL.dat", "w")
x_vals = []
y_vals = []

Nof = 10 #number of files

for i in range(Nof):
    file = open(f"REvsPI.dat-{i}", 'r')
    tmp = []
    for line in file:
        vals = line.split()
        if i == 0:
            x_vals.append(float(vals[0]))
        tmp.append(float(vals[1]))
    y_vals.append(np.array(tmp))

y_vals_final = sum(np.array(y_vals))/Nof

x_vals = [np.log10(x) for x in x_vals]

outFile.write("log10(Re)\tPI\n")
for x, y in zip(x_vals, y_vals_final):
    outFile.write(f"{x}\t{y}\n")

plt.plot(x_vals, y_vals_final, 'o')
plt.grid()
plt.ylabel("$\pi$")
plt.xlabel("$\log_{10}{Re}$")
plt.show()