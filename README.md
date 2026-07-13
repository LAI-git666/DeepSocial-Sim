# DeepSocial-Sim

This repository contains the code, saved logs, analysis scripts, tables, figures, and manuscript source for the paper "Prompted Personality Alignment of LLM Agents Under Survival Pressure".

## Model

The simulations used Qwen-Max through the DashScope OpenAI-compatible API.

- Model: `qwen-max`
- Temperature: `0.7`
- Base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`

Set the API key before running new simulations:

```powershell
$env:DASHSCOPE_API_KEY="your_api_key_here"
```

The existing analysis does not require an API key because it uses the saved JSONL logs.

## Data

The experiment consists of 300 runs:

- 2 scarcity conditions: `ABUNDANCE`, `FAMINE`
- 3 homogeneous personality groups: `All_Aggressive`, `All_Altruistic`, `All_Dominant`
- 50 repeated runs per condition

The raw simulation logs are stored in `data/raw_logs/experiment_*.jsonl`.

The repository is organized as follows:

- `src/`: simulation environment, agents, prompts, LLM client, and batch runner.
- `analysis/`: data processing, statistical analysis, action-frequency analysis, plotting, and appendix export scripts.
- `data/raw_logs/`: 300 saved JSONL simulation logs.
- `data/processed/`: derived CSV files used by the analysis.
- `tables/main_text/`: compact table used in the main manuscript.
- `tables/appendix/`: statistical summaries and selected tests suitable for appendix use.
- `tables/supplementary/`: longer run-level tables suitable for supplementary data release.
- `appendix/`: prompt and metric-definition materials.
- `tests/`: manual physics and integration checks.

## Reproduce the analysis

Run the analysis pipeline from the repository root:

```powershell
python analysis/process_data.py
python analysis/statistical_analysis.py
python analysis/analyze_action_frequency.py
python analysis/plot_results.py
python analysis/export_appendix_materials.py
```

The scripts generate:

- `data/processed/all_actions.csv`
- `data/processed/experiment_summary.csv`
- `data/processed/agent_outcomes.csv`
- `tables/main_text/cross_tab_personality_class.csv`
- `tables/appendix/stats_summary.csv`
- `tables/appendix/stats_tests.csv`
- `tables/appendix/action_frequency_summary.csv`
- `tables/appendix/action_frequency_tests.csv`
- `tables/supplementary/action_frequency_by_run.csv`
- `plots/*.png`
- `appendix/prompt_templates.md`
- `appendix/metric_definitions.md`

## Notes

Class assignment is fixed in the simulator: Kai is Poor, Elala is Middle, and Jax is Rich. The paper should describe this as a fixed initial endowment design, not random class assignment.

The analysis scripts use deterministic keyword and action rules. They do not use LLM-as-a-judge scoring.
