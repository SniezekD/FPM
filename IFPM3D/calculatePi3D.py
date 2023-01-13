import numpy as np
import re 

def del_brackets(string :str) -> str:
    return string.replace("(", '').replace(")",'')

def parse_U_file(path: str) -> list:

    U_file = open(path)
    U_values = []
    tmp_file = open("tmp",'w')

    for line in U_file:
        if re.match(r"^\W([0-9])", line):
            vels = line.split()
            vels = [float(del_brackets(v)) for v in vels]
            U_values.append(vels)

    return U_values

def calc_e(u : float, v : float) -> float:
    return u**2 + v**2

def calc_q(e : float, e_tot : float):
    return e/e_tot

def calculate_PI(U_values: list) -> float:
    n = len(U_values)
    e_values = [calc_e(u[0],u[1]) for u in U_values]
    e_tot = sum(e_values)
    q_values = [calc_q(e,e_tot) for e in e_values]
    q_values_sq = [q**2 for q in q_values]
    nsum = n*sum(q_values_sq)
    return nsum**(-1)


def get_Pi(U_file_path: str) -> float:
    U_values = parse_U_file(U_file_path)
    pi = calculate_PI(U_values)
    return pi
