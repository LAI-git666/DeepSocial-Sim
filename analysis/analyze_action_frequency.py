import csv
import math
import os
from collections import Counter, defaultdict
from statistics import mean, stdev


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACTION_PATH = os.path.join(ROOT_DIR, "data", "processed", "all_actions.csv")
APPENDIX_TABLE_DIR = os.path.join(ROOT_DIR, "tables", "appendix")
SUPPLEMENTARY_TABLE_DIR = os.path.join(ROOT_DIR, "tables", "supplementary")
PLOT_DIR = os.path.join(ROOT_DIR, "plots")
PRODUCTIVE_ACTIONS = {"gather", "eat"}
SOCIAL_ACTIONS = {"talk", "give", "rob"}


try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None

try:
    from scipy import stats as scipy_stats
except Exception:
    scipy_stats = None


def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    if not rows:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def describe(values):
    n = len(values)
    if n == 0:
        return {"N": 0, "Mean": "", "SD": "", "SE": "", "CI95_Low": "", "CI95_High": ""}
    avg = mean(values)
    sd = stdev(values) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n else 0.0
    margin = 1.96 * se
    return {"N": n, "Mean": avg, "SD": sd, "SE": se, "CI95_Low": avg - margin, "CI95_High": avg + margin}


def welch_t(values_a, values_b):
    if len(values_a) < 2 or len(values_b) < 2:
        return "", ""
    if scipy_stats is not None:
        result = scipy_stats.ttest_ind(values_a, values_b, equal_var=False)
        return float(result.statistic), float(result.pvalue)
    avg_a, avg_b = mean(values_a), mean(values_b)
    var_a, var_b = stdev(values_a) ** 2, stdev(values_b) ** 2
    denom = math.sqrt(var_a / len(values_a) + var_b / len(values_b))
    statistic = (avg_a - avg_b) / denom if denom else 0.0
    return statistic, math.erfc(abs(statistic) / math.sqrt(2))


def build_run_level_counts(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["Run_ID"]].append(row)

    run_rows = []
    for run_id, action_rows in sorted(grouped.items()):
        counts = Counter(row["Action"] for row in action_rows)
        total = sum(counts.values())
        scarcity = action_rows[0]["Scarcity"]
        group = action_rows[0]["Group"]
        personality = action_rows[0].get("Personality", group.replace("All_", ""))
        talk = counts.get("talk", 0)
        gather = counts.get("gather", 0)
        productive = sum(counts.get(action, 0) for action in PRODUCTIVE_ACTIONS)
        social = sum(counts.get(action, 0) for action in SOCIAL_ACTIONS)

        run_rows.append({
            "Run_ID": run_id,
            "Scarcity": scarcity,
            "Group": group,
            "Personality": personality,
            "Total_Actions": total,
            "Talk_Count": talk,
            "Gather_Count": gather,
            "Rob_Count": counts.get("rob", 0),
            "Give_Count": counts.get("give", 0),
            "Eat_Count": counts.get("eat", 0),
            "Move_Count": counts.get("move", 0),
            "Idle_Count": counts.get("idle", 0),
            "Talk_Rate": talk / total if total else 0,
            "Gather_Rate": gather / total if total else 0,
            "Talk_Gather_Ratio": talk / gather if gather else "",
            "Social_Rate": social / total if total else 0,
            "Productive_Rate": productive / total if total else 0,
        })
    return run_rows


def summarize_run_counts(run_rows):
    metric_columns = [
        "Talk_Count", "Gather_Count", "Rob_Count", "Give_Count", "Eat_Count",
        "Talk_Rate", "Gather_Rate", "Social_Rate", "Productive_Rate",
    ]
    grouped = defaultdict(list)
    for row in run_rows:
        grouped[(row["Scarcity"], row["Personality"], row["Group"])].append(row)

    summary = []
    for (scarcity, personality, group), rows in sorted(grouped.items()):
        for metric in metric_columns:
            values = [float(row[metric]) for row in rows if row[metric] != ""]
            summary.append({
                "Scarcity": scarcity,
                "Personality": personality,
                "Group": group,
                "Metric": metric,
                **describe(values),
            })
    return summary


def test_abundance_paradox(run_rows):
    tests = []
    metrics = ["Talk_Count", "Gather_Count", "Talk_Rate", "Gather_Rate", "Social_Rate", "Productive_Rate"]
    personalities = sorted({row["Personality"] for row in run_rows})
    for personality in personalities:
        for metric in metrics:
            abundance = [float(row[metric]) for row in run_rows if row["Personality"] == personality and row["Scarcity"] == "ABUNDANCE"]
            famine = [float(row[metric]) for row in run_rows if row["Personality"] == personality and row["Scarcity"] == "FAMINE"]
            statistic, p_value = welch_t(abundance, famine)
            tests.append({
                "Test": "Welch t-test",
                "Metric": metric,
                "Comparison": f"ABUNDANCE vs FAMINE within {personality}",
                "Statistic": statistic,
                "P_Value": p_value,
                "Notes": "Positive statistic means ABUNDANCE is higher.",
            })
    return tests


def plot_talk_gather(summary_rows):
    if plt is None:
        print("matplotlib is not available; skipped action-frequency plot.")
        return

    os.makedirs(PLOT_DIR, exist_ok=True)
    personalities = sorted({row["Personality"] for row in summary_rows})
    scarcity_order = ["ABUNDANCE", "FAMINE"]
    labels = [f"{personality}\n{scarcity}" for personality in personalities for scarcity in scarcity_order]
    x_positions = list(range(len(labels)))
    width = 0.36

    def lookup(metric, personality, scarcity, field):
        for row in summary_rows:
            if row["Metric"] == metric and row["Personality"] == personality and row["Scarcity"] == scarcity:
                return float(row[field])
        return 0.0

    plt.figure(figsize=(11, 6))
    for offset, metric in [(-width / 2, "Talk_Rate"), (width / 2, "Gather_Rate")]:
        means = [lookup(metric, personality, scarcity, "Mean") for personality in personalities for scarcity in scarcity_order]
        errors = [lookup(metric, personality, scarcity, "SE") for personality in personalities for scarcity in scarcity_order]
        plt.bar([x + offset for x in x_positions], means, width=width, yerr=errors, capsize=4, label=metric.replace("_", " "))

    plt.xticks(x_positions, labels)
    plt.ylabel("Mean action share per run (SE)")
    plt.title("Talk vs. Gather Frequency by Personality and Scarcity")
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, "5_action_frequency.png"), dpi=300)
    print("Saved plots/5_action_frequency.png")


def main():
    if not os.path.exists(ACTION_PATH):
        raise FileNotFoundError("Run analysis/process_data.py before analyze_action_frequency.py")

    rows = read_csv(ACTION_PATH)
    run_rows = build_run_level_counts(rows)
    summary_rows = summarize_run_counts(run_rows)
    test_rows = test_abundance_paradox(run_rows)

    write_csv(os.path.join(SUPPLEMENTARY_TABLE_DIR, "action_frequency_by_run.csv"), run_rows)
    write_csv(os.path.join(APPENDIX_TABLE_DIR, "action_frequency_summary.csv"), summary_rows)
    write_csv(os.path.join(APPENDIX_TABLE_DIR, "action_frequency_tests.csv"), test_rows)
    plot_talk_gather(summary_rows)
    print("Saved action-frequency tables.")
    if scipy_stats is None:
        print("Warning: scipy is not available; t-test p-values use a normal approximation.")


if __name__ == "__main__":
    main()
