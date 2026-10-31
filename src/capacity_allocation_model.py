# -*- coding: utf-8 -*-
"""
Generator Rental Fleet Revenue Management

Linear programming capacity-allocation model that decides, for each week and
rental duration, how many rental requests to accept in order to maximise
revenue subject to fleet-capacity and demand constraints.
"""

import pandas as pd
import numpy as np
from pyomo.environ import *

# Read in the data

file_name  = "../data/generator_rental_dataset.xlsx"
df = pd.read_excel(file_name, 'Data', header=None)
durations  = [1, 4, 8, 16]
fleet_size = int(df.iloc[2, 1])       #fleet size=300
unit_cost  = int(df.iloc[4, 1])       #unit cost=3000
initial_inv = int(df.iloc[3, 1])      #initial inventory=77


# Extract data
df_data = pd.DataFrame(df.iloc[10:62, :20])
df_data.columns = [
    "date", "wk_no", "inventory", "total_accpt",
    "p1",  "d1",  "a1",  "ret1",
    "p4",  "d4",  "a4",  "ret4",
    "p8",  "d8",  "a8",  "ret8",
    "p16", "d16", "a16", "ret16",
]

df_data = df_data.set_index("wk_no")

weeks = [w for w in df_data.index if 1 < w < 52]
n_weeks = len(weeks)
n_durations = len(durations)

# Arrays

price_np = np.array([
    [df_data.loc[w, f"p{d}"] for d in durations]
    for w in weeks
])

demand_np = np.array([
    [df_data.loc[w, f"d{d}"] for d in durations]
    for w in weeks
])

actual_np = np.array([
    [df_data.loc[w, f"a{d}"] for d in durations]
    for w in weeks
])

# Get actual values for accepted rentals from the dataset

def actual_accept(week, duration):
    if week in df_data.index and week >= 2:
        return df_data.loc[week, f"a{duration}"]
    return 0

# Returns each week

additional_returns= []

for w in weeks:
    extra_returns = 0
    for d in durations:
        actual_returns = df_data.loc[w, f"ret{d}"]
        expected_returns = actual_accept(w - d, d)
        extra_returns += max(0, actual_returns - expected_returns)
    additional_returns.append(extra_returns)

# Available inventory 

I = []
returned_gen = 0

for w in range(n_weeks):
    returned_gen += additional_returns[w]
    I.append(initial_inv + returned_gen)
    
    
# Model

model = ConcreteModel()

# Variable

model.x = Var(range(n_weeks), range(n_durations), domain=NonNegativeReals)
    
# Objective function

def obj_rule(model):
    return sum(
        7 * price_np[w, d] * durations[d] * model.x[w, d]
        for w in range(n_weeks)
        for d in range(n_durations)
    )

model.obj = Objective(rule=obj_rule, sense=maximize)


# Demand constraints

def demand_rule(model, w, d):
    return model.x[w,d] <= demand_np[w,d]

model.demand_const = Constraint(range(n_weeks), range(n_durations), rule=demand_rule)


# Capacity constraints


def capacity_rule(model, c):
    return sum(
        model.x[w, d]
        for w in range(n_weeks)
        for d in range(n_durations)
        if w <= c <= w + durations[d] - 1
    ) <= I[c]

model.capacity_const = Constraint(range(n_weeks), rule=capacity_rule)

# Solve
solver = SolverFactory("glpk")
results = solver.solve(model)

# Print Results
actual_revenue = sum(
    7 * durations[d] * price_np[w, d] * actual_np[w, d]
    for w in range(n_weeks)
    for d in range(n_durations)
)

optimised_revenue = value(model.obj)

print("REVENUE")
print("Actual Revenue:", round(actual_revenue, 2))
print("Optimised Revenue:", round(optimised_revenue, 2))

# Load factor

# Actual weekly load factor for all 52 weeks
actual_lf_by_week = {
    w: (fleet_size - df_data.loc[w, "inventory"]) / fleet_size
    for w in range(1, 53)
}

actual_load_factor = np.mean(list(actual_lf_by_week.values()))

# Store optimised inventory by week
opt_I = {1: initial_inv}

for c in weeks:
    rented_gen = sum(
        value(model.x[w, d])
        for w in range(n_weeks)
        for d in range(n_durations)
        if weeks[w] < c < weeks[w] + durations[d]
    )
    opt_I[c] = I[c - 2] - rented_gen

# Approximate week 52 inventory
accepted_51 = sum(value(model.x[weeks.index(51), d]) for d in range(n_durations))
opt_I[52] = max(0, opt_I[51] - accepted_51)

# Optimised weekly load factor
optimised_lf_by_week = {
    w: (fleet_size - opt_I[w]) / fleet_size
    for w in range(1, 53)
}

optimised_load_factor = np.mean(list(optimised_lf_by_week.values()))

print()
print("LOAD FACTOR")
print("Actual Load Factor:", round(actual_load_factor, 4))
print("Optimised Load Factor:", round(optimised_load_factor, 4))

# ROI
actual_roi = actual_revenue / (fleet_size * unit_cost)
optimised_roi = optimised_revenue / (fleet_size * unit_cost)

print()
print("ROI")
print("Actual ROI:", round(actual_roi, 2))
print("Optimised ROI:", round(optimised_roi, 2))


# SAVE RESULTS TO EXCEL

# 1. Summary table by rental length
summary_rows = []
for d_idx, d in enumerate(durations):
    summary_rows.append({
        "Rental Length": d,
        "Demand": int(sum(demand_np[w, d_idx] for w in range(n_weeks))),
        "Actual": int(sum(actual_np[w, d_idx] for w in range(n_weeks))),
        "Optimised": round(sum(value(model.x[w, d_idx]) for w in range(n_weeks)), 2),
    })

summary_df = pd.DataFrame(summary_rows)

# 2. Weekly load factor table
weekly_lf_df = pd.DataFrame({
    "wk_no": list(range(1, 53)),
    "actual_load_factor": [round(actual_lf_by_week[w], 4) for w in range(1, 53)],
    "optimised_load_factor": [round(optimised_lf_by_week[w], 4) for w in range(1, 53)],
})

# 3. Save into one Excel file with two sheets
with pd.ExcelWriter("results.xlsx", engine="openpyxl") as writer:
    summary_df.to_excel(writer, sheet_name="Summary", index=False)
    weekly_lf_df.to_excel(writer, sheet_name="Weekly_Load_Factor", index=False)

