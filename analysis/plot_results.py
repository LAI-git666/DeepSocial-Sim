import os
import csv
import math
from collections import Counter, defaultdict
from statistics import mean, stdev

import matplotlib.pyplot as plt

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(ROOT_DIR, "data", "processed")
OUTPUT_DIR = os.path.join(ROOT_DIR, "plots")
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)


SCARCITY_ORDER = ["ABUNDANCE", "FAMINE"]
PERSONALITY_ORDER = ["Aggressive", "Altruistic", "Dominant"]
GROUP_ORDER = [f"All_{personality}" for personality in PERSONALITY_ORDER]
COLORS = {"Aggressive": "#C44E52", "Altruistic": "#55A868", "Dominant": "#4C72B0"}


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def to_float(value):
    return float(value) if value not in ("", None) else math.nan


def describe(values):
    values = [v for v in values if not math.isnan(v)]
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    avg = mean(values)
    se = (stdev(values) / math.sqrt(n)) if n > 1 else 0.0
    return avg, se


def load_data():
    try:
        df_actions = read_csv(os.path.join(PROCESSED_DIR, "all_actions.csv"))
        df_summary = read_csv(os.path.join(PROCESSED_DIR, "experiment_summary.csv"))
        return df_actions, df_summary
    except FileNotFoundError:
        print("CSV files not found. Please run analysis/process_data.py first.")
        return None, None


def plot_survival_curve(df_summary):
    """Survival count by scarcity and personality, with SE error bars."""
    grouped = defaultdict(list)
    for row in df_summary:
        grouped[(row["Group"], row["Scarcity"])].append(to_float(row["Survival_Count"]))

    labels = GROUP_ORDER
    x_positions = list(range(len(labels)))
    width = 0.36

    plt.figure(figsize=(10, 6))
    for offset, scarcity in [(-width / 2, "ABUNDANCE"), (width / 2, "FAMINE")]:
        values = []
        errors = []
        for group in labels:
            avg, se = describe(grouped[(group, scarcity)])
            values.append(avg)
            errors.append(se)
        plt.bar([x + offset for x in x_positions], values, width=width, yerr=errors, capsize=4, label=scarcity)

    plt.xticks(x_positions, labels, rotation=15)
    plt.title("Survival Rate by Personality & Scarcity")
    plt.ylabel("Mean survivors per run (SE)")
    plt.xlabel("Personality Group")
    plt.legend(title="Scarcity Mode")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/1_survival_rate.png", dpi=300)
    print("Plot 1 saved: Survival Rate")


def plot_hypocrisy_heatmap(df_summary):
    """Average hypocrisy count per run."""
    matrix = []
    for group in GROUP_ORDER:
        row_values = []
        for scarcity in SCARCITY_ORDER:
            values = [
                to_float(row["Total_Hypocrisy"])
                for row in df_summary
                if row["Group"] == group and row["Scarcity"] == scarcity
            ]
            avg, _ = describe(values)
            row_values.append(avg)
        matrix.append(row_values)

    plt.figure(figsize=(8, 6))
    image = plt.imshow(matrix, cmap="YlOrRd", aspect="auto")
    plt.colorbar(image, label="Mean count per run")
    plt.xticks(range(len(SCARCITY_ORDER)), SCARCITY_ORDER)
    plt.yticks(range(len(GROUP_ORDER)), GROUP_ORDER)
    for y, row_values in enumerate(matrix):
        for x, value in enumerate(row_values):
            plt.text(x, y, f"{value:.1f}", ha="center", va="center", color="black")
    plt.title("Average Hypocrisy Count per Run")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/2_hypocrisy_heatmap.png", dpi=300)
    print("Plot 2 saved: Hypocrisy Heatmap")


def plot_class_fate(df_summary):
    """First casualty counts by class."""
    classes = ["Poor", "Middle", "Rich"]
    grouped = defaultdict(Counter)
    for row in df_summary:
        if row["Who_Died_First"] != "None":
            grouped[row["Group"]][row["Who_Died_First"]] += 1

    if not grouped:
        print("No deaths recorded, skipping Plot 3.")
        return

    plt.figure(figsize=(10, 6))
    width = 0.25
    x_positions = list(range(len(GROUP_ORDER)))
    for index, cls in enumerate(classes):
        offset = (index - 1) * width
        counts = [grouped[group].get(cls, 0) for group in GROUP_ORDER]
        plt.bar([x + offset for x in x_positions], counts, width=width, label=cls)

    plt.xticks(x_positions, GROUP_ORDER, rotation=15)
    plt.title("First Casualty by Social Class")
    plt.ylabel("Count of Runs")
    plt.xlabel("Personality Group")
    plt.legend(title="Who Died First?")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/3_class_fate.png", dpi=300)
    print("Plot 3 saved: Class Fate")


def plot_alignment_decay(df_actions):
    """Persona collapse rate over numeric energy bins, with SE ribbons."""
    grouped = defaultdict(list)
    for row in df_actions:
        energy = to_float(row["Energy"])
        if math.isnan(energy) or energy < 0 or energy > 100:
            continue
        energy_bin = int(energy // 5) * 5
        if energy_bin == 100:
            energy_bin = 95
        personality = row.get("Personality") or row["Group"].replace("All_", "")
        grouped[(personality, row["Scarcity"], energy_bin)].append(to_float(row["Is_Misaligned"]))

    if not grouped:
        print("No valid action data found, skipping Plot 4.")
        return

    plt.figure(figsize=(12, 8))
    for personality in PERSONALITY_ORDER:
        for scarcity in SCARCITY_ORDER:
            xs = []
            means = []
            ses = []
            for energy_bin in range(0, 100, 5):
                values = grouped.get((personality, scarcity, energy_bin), [])
                if not values:
                    continue
                avg, se = describe(values)
                xs.append(energy_bin + 2.5)
                means.append(avg)
                ses.append(se)
            if not xs:
                continue
            linestyle = "-" if scarcity == "ABUNDANCE" else "--"
            label = f"{personality} / {scarcity}"
            color = COLORS[personality]
            lower = [max(0, avg - se) for avg, se in zip(means, ses)]
            upper = [min(1, avg + se) for avg, se in zip(means, ses)]
            plt.plot(xs, means, marker="o", linewidth=2, linestyle=linestyle, label=label, color=color)
            plt.fill_between(xs, lower, upper, color=color, alpha=0.12)

    plt.gca().invert_xaxis()
    plt.title("Probability of Persona Collapse vs. Energy Level (All Groups)", fontsize=16)
    plt.ylabel("Persona Collapse Rate PCR(E) (SE)", fontsize=14)
    plt.xlabel("Energy Level (High -> Low)", fontsize=14)
    plt.legend(title="Condition", bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.ylim(-0.02, 1.02)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/4_alignment_decay.png", dpi=300)
    print("Plot 4 saved: Alignment Decay")


def main():
    print("Starting visualization...")
    df_actions, df_summary = load_data()

    if df_actions is not None:
        plot_survival_curve(df_summary)
        plot_hypocrisy_heatmap(df_summary)
        plot_class_fate(df_summary)
        plot_alignment_decay(df_actions)
        print("All plots saved to 'plots/' directory.")

if __name__ == "__main__":
    main()