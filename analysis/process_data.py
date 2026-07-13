import os
import json
import csv
from metrics import is_hypocritical, is_misaligned, personality_from_group

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT_DIR, "data", "raw_logs")
PROCESSED_DIR = os.path.join(ROOT_DIR, "data", "processed")
MAIN_TABLE_DIR = os.path.join(ROOT_DIR, "tables", "main_text")
ROLE_MAP = {"Kai": "Poor", "Elala": "Middle", "Jax": "Rich"}


def write_csv(path, rows):
    if not rows:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def process_logs():
    all_actions_rows = []
    summary_rows = []
    agent_outcome_rows = []

    if not os.path.exists(LOG_DIR):
        print(f"Error: Directory '{LOG_DIR}' not found.")
        return

    files = [f for f in os.listdir(LOG_DIR) if f.startswith("experiment_") and f.endswith(".jsonl")]
    if not files:
        print(f"No experiment logs found in {LOG_DIR}.")
        return

    print(f"Processing {len(files)} log files...")

    for filename in files:
        filepath = os.path.join(LOG_DIR, filename)
        try:
            parts = filename.replace("experiment_", "").replace(".jsonl", "").split("_")
            scarcity = parts[0]
            group = "_".join(parts[1:-1])
            run_id = filename.replace(".jsonl", "")
        except Exception:
            print(f"Skipping malformed filename: {filename}")
            continue

        personality = personality_from_group(group)
        first_death_turn = 50
        who_died_first = "None"
        total_robs = 0
        total_hypocrisy = 0
        poor_first_crime = None
        rich_first_crime = None
        survivors = {"Kai", "Elala", "Jax"}
        agent_death_turn = {name: None for name in ROLE_MAP}

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    turn_data = json.loads(line)
                    turn = turn_data["turn"]

                    for agent_data in turn_data["agents"]:
                        name = agent_data["name"]
                        status = agent_data["status"]
                        internal = agent_data["internal"]
                        external = agent_data["external"]

                        cls = ROLE_MAP.get(name, "Unknown")
                        action = external.get("action", "idle")
                        thought = internal.get("thought", "") or ""
                        content = external.get("content", "") or ""

                        hypocrisy = is_hypocritical(thought, action, content)
                        misaligned = is_misaligned(personality, action, thought, content)

                        all_actions_rows.append({
                            "Run_ID": run_id,
                            "Scarcity": scarcity,
                            "Group": group,
                            "Personality": personality,
                            "Turn": turn,
                            "Agent": name,
                            "Class": cls,
                            "Energy": status["energy"],
                            "Inventory": status.get("inv", status.get("inventory", 0)),
                            "Action": action,
                            "Thought": thought,
                            "Speech": content,
                            "Is_Hypocrisy": 1 if hypocrisy else 0,
                            "Is_Misaligned": 1 if misaligned else 0,
                        })

                        if action == "rob":
                            total_robs += 1
                            if cls == "Poor" and poor_first_crime is None:
                                poor_first_crime = turn
                            if cls == "Rich" and rich_first_crime is None:
                                rich_first_crime = turn

                        if hypocrisy:
                            total_hypocrisy += 1

                        if status["dead"]:
                            if agent_death_turn[name] is None:
                                agent_death_turn[name] = turn
                            if name in survivors:
                                survivors.remove(name)
                                if turn < first_death_turn:
                                    first_death_turn = turn
                                    who_died_first = cls
                except json.JSONDecodeError:
                    continue

        summary_rows.append({
            "Run_ID": run_id,
            "Scarcity": scarcity,
            "Group": group,
            "Personality": personality,
            "Survival_Count": len(survivors),
            "First_Death_Turn": first_death_turn if len(survivors) < 3 else 50,
            "Who_Died_First": who_died_first,
            "Total_Robs": total_robs,
            "Total_Hypocrisy": total_hypocrisy,
            "Poor_First_Crime_Turn": poor_first_crime if poor_first_crime is not None else 50,
            "Rich_First_Crime_Turn": rich_first_crime if rich_first_crime is not None else 50,
        })

        for name, cls in ROLE_MAP.items():
            died = agent_death_turn[name] is not None
            agent_outcome_rows.append({
                "Run_ID": run_id,
                "Scarcity": scarcity,
                "Group": group,
                "Personality": personality,
                "Agent": name,
                "Class": cls,
                "Died": int(died),
                "Death_Turn": agent_death_turn[name] if died else 50,
                "First_Casualty": int(who_died_first == cls),
                "Survived_Run": int(not died),
            })

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(MAIN_TABLE_DIR, exist_ok=True)

    if all_actions_rows:
        write_csv(os.path.join(PROCESSED_DIR, "all_actions.csv"), all_actions_rows)
        print(f"Saved data/processed/all_actions.csv ({len(all_actions_rows)} rows)")

    if summary_rows:
        write_csv(os.path.join(PROCESSED_DIR, "experiment_summary.csv"), summary_rows)
        print(f"Saved data/processed/experiment_summary.csv ({len(summary_rows)} rows)")

    if agent_outcome_rows:
        write_csv(os.path.join(PROCESSED_DIR, "agent_outcomes.csv"), agent_outcome_rows)
        grouped = {}
        for row in agent_outcome_rows:
            key = (row["Personality"], row["Class"], row["Scarcity"])
            grouped.setdefault(key, []).append(row)

        cross_tab = []
        for (personality, cls, scarcity), rows in sorted(grouped.items()):
            n = len(rows)
            cross_tab.append({
                "Personality": personality,
                "Class": cls,
                "Scarcity": scarcity,
                "N": n,
                "Death_Rate": sum(int(r["Died"]) for r in rows) / n,
                "First_Casualty_Rate": sum(int(r["First_Casualty"]) for r in rows) / n,
                "Survival_Rate": sum(int(r["Survived_Run"]) for r in rows) / n,
            })
        write_csv(os.path.join(MAIN_TABLE_DIR, "cross_tab_personality_class.csv"), cross_tab)
        print("Saved data/processed/agent_outcomes.csv and tables/main_text/cross_tab_personality_class.csv")


if __name__ == "__main__":
    process_logs()
