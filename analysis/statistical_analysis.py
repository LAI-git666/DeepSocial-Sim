import csv
import math
import os
from collections import defaultdict
from statistics import mean, stdev


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(ROOT_DIR, "data", "processed")
TABLE_DIR = os.path.join(ROOT_DIR, "tables", "appendix")
SUMMARY_PATH = os.path.join(PROCESSED_DIR, "experiment_summary.csv")
AGENT_OUTCOMES_PATH = os.path.join(PROCESSED_DIR, "agent_outcomes.csv")


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


def as_float(row, column):
    value = row.get(column, "")
    if value == "" or value is None:
        return math.nan
    return float(value)


def describe(values):
    values = [v for v in values if not math.isnan(v)]
    n = len(values)
    if n == 0:
        return {"N": 0, "Mean": "", "SD": "", "SE": "", "CI95_Low": "", "CI95_High": ""}

    avg = mean(values)
    sd = stdev(values) if n > 1 else 0.0
    se = sd / math.sqrt(n) if n > 0 else 0.0
    margin = 1.96 * se
    return {
        "N": n,
        "Mean": avg,
        "SD": sd,
        "SE": se,
        "CI95_Low": avg - margin,
        "CI95_High": avg + margin,
    }


def cohen_d(values_a, values_b):
    values_a = [v for v in values_a if not math.isnan(v)]
    values_b = [v for v in values_b if not math.isnan(v)]
    if len(values_a) < 2 or len(values_b) < 2:
        return ""
    sd_a = stdev(values_a)
    sd_b = stdev(values_b)
    pooled = math.sqrt(((len(values_a) - 1) * sd_a ** 2 + (len(values_b) - 1) * sd_b ** 2) / (len(values_a) + len(values_b) - 2))
    if pooled == 0:
        return 0.0
    return (mean(values_a) - mean(values_b)) / pooled


def welch_t(values_a, values_b):
    values_a = [v for v in values_a if not math.isnan(v)]
    values_b = [v for v in values_b if not math.isnan(v)]
    if len(values_a) < 2 or len(values_b) < 2:
        return "", "", ""
    if scipy_stats is not None:
        result = scipy_stats.ttest_ind(values_a, values_b, equal_var=False)
        statistic = float(result.statistic)
        p_value = float(result.pvalue)
    else:
        avg_a, avg_b = mean(values_a), mean(values_b)
        var_a, var_b = stdev(values_a) ** 2, stdev(values_b) ** 2
        denom = math.sqrt(var_a / len(values_a) + var_b / len(values_b))
        statistic = (avg_a - avg_b) / denom if denom else 0.0
        p_value = math.erfc(abs(statistic) / math.sqrt(2))
    return statistic, p_value, cohen_d(values_a, values_b)


def anova(groups):
    clean_groups = [[v for v in values if not math.isnan(v)] for values in groups]
    clean_groups = [values for values in clean_groups if len(values) > 1]
    if len(clean_groups) < 2:
        return "", ""
    if scipy_stats is not None:
        result = scipy_stats.f_oneway(*clean_groups)
        return float(result.statistic), float(result.pvalue)
    return "", ""


def chi_square(rows, group_column, outcome_column, outcome_values):
    table = defaultdict(lambda: defaultdict(int))
    for row in rows:
        table[row[group_column]][row[outcome_column]] += 1
    groups = sorted(table)
    observed = [[table[group].get(value, 0) for value in outcome_values] for group in groups]
    if scipy_stats is not None and len(groups) > 1:
        result = scipy_stats.chi2_contingency(observed)
        return float(result.statistic), float(result.pvalue), str(observed)
    return "", "", str(observed)


def summarize_experiment_metrics(summary_rows):
    metric_columns = ["Survival_Count", "First_Death_Turn", "Total_Robs", "Total_Hypocrisy"]
    output = []
    grouped = defaultdict(list)
    for row in summary_rows:
        grouped[(row["Scarcity"], row["Personality"], row["Group"])].append(row)

    for (scarcity, personality, group), rows in sorted(grouped.items()):
        for metric in metric_columns:
            output.append({
                "Scarcity": scarcity,
                "Personality": personality,
                "Group": group,
                "Metric": metric,
                **describe([as_float(row, metric) for row in rows]),
            })
    return output


def test_experiment_metrics(summary_rows):
    tests = []
    metric_columns = ["Survival_Count", "First_Death_Turn", "Total_Robs", "Total_Hypocrisy"]
    personalities = sorted({row["Personality"] for row in summary_rows})
    scarcities = sorted({row["Scarcity"] for row in summary_rows})

    for metric in metric_columns:
        for personality in personalities:
            abundance = [as_float(row, metric) for row in summary_rows if row["Personality"] == personality and row["Scarcity"] == "ABUNDANCE"]
            famine = [as_float(row, metric) for row in summary_rows if row["Personality"] == personality and row["Scarcity"] == "FAMINE"]
            statistic, p_value, effect = welch_t(abundance, famine)
            tests.append({
                "Test": "Welch t-test",
                "Metric": metric,
                "Comparison": f"ABUNDANCE vs FAMINE within {personality}",
                "Statistic": statistic,
                "P_Value": p_value,
                "Effect_Size": effect,
                "Notes": "Cohen_d reports ABUNDANCE - FAMINE",
            })

        for scarcity in scarcities:
            groups = [
                [as_float(row, metric) for row in summary_rows if row["Personality"] == personality and row["Scarcity"] == scarcity]
                for personality in personalities
            ]
            statistic, p_value = anova(groups)
            tests.append({
                "Test": "One-way ANOVA",
                "Metric": metric,
                "Comparison": f"Personality groups within {scarcity}",
                "Statistic": statistic,
                "P_Value": p_value,
                "Effect_Size": "",
                "Notes": "Groups: " + ", ".join(personalities),
            })
    return tests


def test_agent_outcomes(agent_rows):
    tests = []
    for scarcity in sorted({row["Scarcity"] for row in agent_rows}):
        subset = [row for row in agent_rows if row["Scarcity"] == scarcity]
        for metric in ["Died", "First_Casualty"]:
            statistic, p_value, observed = chi_square(subset, "Class", metric, ["0", "1"])
            tests.append({
                "Test": "Chi-square",
                "Metric": metric,
                "Comparison": f"Class {metric} difference within {scarcity}",
                "Statistic": statistic,
                "P_Value": p_value,
                "Effect_Size": "",
                "Notes": observed,
            })
    return tests


def main():
    if not os.path.exists(SUMMARY_PATH):
        raise FileNotFoundError("Run analysis/process_data.py before statistical_analysis.py")

    summary_rows = read_csv(SUMMARY_PATH)
    stats_summary = summarize_experiment_metrics(summary_rows)
    stats_tests = test_experiment_metrics(summary_rows)

    if os.path.exists(AGENT_OUTCOMES_PATH):
        stats_tests.extend(test_agent_outcomes(read_csv(AGENT_OUTCOMES_PATH)))

    write_csv(os.path.join(TABLE_DIR, "stats_summary.csv"), stats_summary)
    write_csv(os.path.join(TABLE_DIR, "stats_tests.csv"), stats_tests)
    print("Saved tables/appendix/stats_summary.csv and tables/appendix/stats_tests.csv")
    if scipy_stats is None:
        print("Warning: scipy is not available; t-test p-values use a normal approximation and ANOVA/chi-square p-values are blank.")


if __name__ == "__main__":
    main()
