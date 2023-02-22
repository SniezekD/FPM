import matplotlib.pyplot as plt
import numpy as np

Nof = 7 #number of files
nameTemplate = "results"

outFilePi = open("resultsPI_ALL.dat", "w")
x_valsPi = []
y_valsPi = []
y_vals_T = []

x_vals_f = []
y_vals_f = []

for i in range(Nof):
    file = open(f"{nameTemplate}-{i}.dat", 'r')
    tmpPi = []
    tmp_f = []
    tmp_T = []
    for line in file:
        try:
            vals = line.split()
            if i == 0:
                x_valsPi.append(float(vals[0]))
                x_vals_f.append(float(vals[3]))
            tmpPi.append(float(vals[1]))
            tmp_f.append(float(vals[2]))
            tmp_T.append(float(vals[4]))
        except:
            pass

    y_valsPi.append(np.array(tmpPi))
    y_vals_f.append(np.array(tmp_f))
    y_vals_T.append(np.array(tmp_T))

y_valsPi_final = sum(np.array(y_valsPi))/Nof
y_vals_f_final = sum(-1*np.array(y_vals_f))/Nof
y_vals_T_final = sum(np.array(y_vals_T))/Nof

std_dev_Pi = []
std_dev_T = []
for i in range(len(y_valsPi[0])):
    tmp_pi_vec = [y_valsPi[k][i] for k in range(len(y_valsPi))]
    mean = np.mean(tmp_pi_vec)
    n = len(tmp_pi_vec)
    s = sum([(j - mean)**2 for j in tmp_pi_vec])
    std_dev = np.sqrt(s/(n-1))
    std_err = std_dev/np.sqrt(n)
    std_dev_Pi.append(std_err)

    tmp_T_vec = [y_vals_T[k][i] for k in range(len(y_vals_T))]
    mean = np.mean(tmp_T_vec)
    nT = len(tmp_T_vec)
    sT = sum([(j - mean)**2 for j in tmp_T_vec])
    std_dev_T_tmp = np.sqrt(sT/(nT-1))
    std_err_T = std_dev_T_tmp/np.sqrt(nT)
    std_dev_T.append(std_err_T)

x_valsPi = [np.log10(x) for x in x_valsPi]
# x_vals_f = [np.log10(x) for x in x_vals_f]
# y_vals_f = [np.log10(y) for y in y_vals_f_final]

outFilePi.write("log10(Re)\tPI,\tstderr(PI)\tT,\tstderr(T)\n")
for x, y, deltay, T, deltaT in zip(x_valsPi, y_valsPi_final, std_dev_Pi, y_vals_T_final, std_dev_T):
    outFilePi.write(f"{x}\t{y}\t{deltay}\t{T}\t{deltaT}\n")

plt.plot(x_valsPi, y_valsPi_final, 'o')
plt.grid()
plt.ylabel("$\pi$")
plt.xlabel("$\log_{10}{Re}$")
plt.ylim(0.35,0.55)
plt.yticks(np.arange(0.35,0.56,0.05))
plt.savefig('PI-vs-log(Re).png')
plt.show()

plt.plot(x_vals_f, y_vals_f_final, 'o')
plt.grid()
plt.ylabel("f")
plt.yscale('log')
plt.xscale('log')
plt.xlabel("Re'")
plt.savefig("f-vs-Re'.png")
plt.show()