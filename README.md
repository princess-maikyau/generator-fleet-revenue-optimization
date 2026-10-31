# Generator Rental Revenue Management

*Capacity allocation for a rental fleet using linear programming*

A linear programming capacity-allocation model that decides, week by week and duration by duration, how many generator rental requests to accept in order to maximise revenue from a fixed fleet — built for the *Pricing Analytics* module of Warwick Business School's MSc Business Analytics.

## Business problem

PowerLease Generators (PLG) rents out a fixed fleet of 300 generators across four rental durations — 1, 4, 8, and 16 weeks. Historically, PLG accepted rental requests on a first-come, first-served basis, which left revenue on the table: short-term, lower-value rentals could crowd out fleet capacity that would otherwise have gone to longer, more profitable rentals later in the year. The question is whether a smarter acceptance policy — one that looks ahead at future demand and inventory — can increase revenue without acquiring a single additional generator.

## Data

52 weeks of 2025 branch-level rental data from the module's PowerLease Generators case study: weekly demand, prices, and accepted/returned units for each of the four rental durations, plus fleet size (300), initial inventory (77 units), and unit cost (£3,000). **The dataset is not included in this repository**, as it was provided by the university for coursework and is not licensed for redistribution. To run the model, place it at `data/generator_rental_dataset.xlsx` (see [`data/README.md`](data/README.md)).

## Methodology

A linear program (`src/capacity_allocation_model.py`, built with [Pyomo](https://www.pyomo.org/) and solved with GLPK) decides `x[w, d]` — how many requests to accept in week `w` for duration `d` — to:

- **Maximise** total revenue, `7 × price × duration × x[w, d]` summed over all weeks and durations.
- **Subject to**: demand constraints (can't accept more than what was actually requested in each week/duration cell) and fleet-capacity constraints (the fleet of generators out on rent at any given week, across all overlapping rental durations, can't exceed the available inventory — recomputed week-by-week from the initial inventory plus units returned early or late).

The model is validated against the real 2025 outcomes: the actual historical acceptance decisions are compared with what the optimiser would have chosen, holding demand and fleet size fixed.

## Key results

| Metric | Actual (2025) | Optimised | Change |
|---|---|---|---|
| Revenue | £4,650,478.70 | £5,116,909.00 | **+10.0%** |
| ROI (revenue ÷ fleet cost) | 5.17 | 5.69 | **+10.0%** |
| Average load factor | 73.4% | 79.1% | **+5.7 pts** |

Simply re-sequencing which requests get accepted — with no change to fleet size or pricing — unlocks roughly £466k in additional annual revenue and pushes fleet utilisation from 73% to 79%, by prioritising the mix of rental durations and timing that the fleet-capacity constraints actually allow for.

## Repository structure

```
src/
  capacity_allocation_model.py   # LP model: data prep, Pyomo model, solve, results export
data/
  README.md                      # how to obtain the (not included) case dataset
```

## Running it

Requires the case dataset in `data/` (not included — see above) and the [GLPK](https://www.gnu.org/software/glpk/) solver to be installed on your system (not a Python package — e.g. `apt install glpk-utils` on Debian/Ubuntu, `brew install glpk` on macOS).

```bash
pip install -r requirements.txt
cd src
python capacity_allocation_model.py
```

This prints the actual-vs-optimised revenue, load factor, and ROI comparison to the console, and writes a two-sheet `results.xlsx` (summary by rental duration, and weekly load factor) into the working directory.

## Tech stack

Python · [Pyomo](https://www.pyomo.org/) (linear programming) · GLPK (solver) · pandas · NumPy · openpyxl

## Attribution

**Team project.** Completed as group coursework (Group 3, Pricing Analytics, MSc Business Analytics, Warwick Business School). The code and analysis in this repository are the team's shared work, published with full credit to the group to show the project; this is not a claim of sole authorship.

## License

MIT — see [LICENSE](LICENSE).
