import matplotlib.pyplot as plt
import numpy as np

Nof = 10 #number of files
nameTemplate = "results.dat"

outFilePi = open("resultsPI_ALL.dat", "w")
x_valsPi = []
y_valsPi = []

x_vals_f = []
y_vals_f = []

for i in range(Nof):
    file = open(f"{nameTemplate}-{i}", 'r')
    tmpPi = []
    tmp_f = []
    for line in file:
        try:
            vals = line.split()
            if i == 0:
                x_valsPi.append(float(vals[0]))
                x_vals_f.append(float(vals[3]))
            tmpPi.append(float(vals[1]))
            tmp_f.append(float(vals[2]))
        except:
            pass

    y_valsPi.append(np.array(tmpPi))
    y_vals_f.append(np.array(tmp_f))

y_valsPi_final = sum(np.array(y_valsPi))/Nof
y_vals_f_final = sum(-1*np.array(y_vals_f))/Nof

x_valsPi = [np.log10(x) for x in x_valsPi]
# x_vals_f = [np.log10(x) for x in x_vals_f]
# y_vals_f = [np.log10(y) for y in y_vals_f_final]

outFilePi.write("log10(Re)\tPI\n")
for x, y in zip(x_valsPi, y_valsPi_final):
    outFilePi.write(f"{x}\t{y}\n")

plt.plot(x_valsPi, y_valsPi_final, 'o')
plt.grid()
plt.ylabel("$\pi$")
plt.xlabel("$\log_{10}{Re}$")
plt.ylim(0.35,0.55)
plt.yticks(np.arange(0.35,0.56,0.05))
plt.show()

plt.plot(x_vals_f, y_vals_f_final, 'o')
plt.grid()
plt.ylabel("f")
plt.yscale('log')
plt.xscale('log')
plt.xlabel("Re'")
plt.show()