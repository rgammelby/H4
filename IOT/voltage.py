import numpy as np

# input voltage
Vcc = 5.0

# LDR minimum and maximum values
LDR_min = 100
LDR_max = 10000000

# fixed resistor n (Ω) calculated by geometric mean of the LDR min and max values. used to calculate greatest voltage swing later
R = np.sqrt(LDR_min * LDR_max)

# generate many random LDR values (log-uniform) to simulate varying light
num_samples = 1000
RL_samples = 10 ** np.random.uniform(2, 7, num_samples)  # 100 Ω → 10 MΩ

# compute divider voltages
#V_samples = Vcc * (R / (R + RL_samples))

# voltage divider formula for lowest and highest possible LDR resistances
V_one = Vcc * (R / (R + 100))
V_two = Vcc * (R / (R + 10000000))

# lowest resistance
print(f"V1: {V_one}")
# highest resistance
print(f"V2: {V_two}")

# calculate the covered percentage of the output voltage span by lowest to highest resistance
result = (V_one - V_two)
percentage = (result / Vcc) * 100
print(f"Percentage result: {percentage} of voltage variance span covered.")

# compute variance
#voltage_variance = np.var(V_samples)

print(f"Fixed R: {R} ohm")
#print(f"Voltage variance over {num_samples} random RL samples: {voltage_variance:.6f} V^2")
#voltage_std = np.sqrt(voltage_variance)
#print(f"Voltage standard deviation: {voltage_std:.6f} V")