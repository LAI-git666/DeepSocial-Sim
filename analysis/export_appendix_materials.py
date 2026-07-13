import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import config
import prompts
from metrics import FRIENDLY_KEYWORDS, MALICIOUS_KEYWORDS, WEAKNESS_KEYWORDS


APPENDIX_DIR = os.path.join(ROOT_DIR, "appendix")


def write_text(path, content):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def bullet_list(items):
    return "\n".join(f"- {item}" for item in items)


def build_prompt_appendix():
    sections = [
        "# Appendix A. Prompt Templates and Model Configuration",
        "",
        "## A.1 Model Configuration",
        "",
        "- Model: Qwen-Max",
        "- API: DashScope OpenAI-compatible API",
        "- Temperature: 0.7",
        "- Response format: JSON requested through prompt instructions; no JSON-mode API parameter was used.",
        "",
        "## A.2 World Rules",
        "",
        "```text",
        prompts.WORLD_RULES.strip(),
        "```",
        "",
        "## A.3 System Prompts",
        "",
    ]

    for personality, template in prompts.PERSONALITY_PROMPTS.items():
        sections.extend([
            f"### {personality}",
            "",
            "```text",
            template.strip(),
            "```",
            "",
        ])

    sections.extend([
        "## A.4 Dynamic Prompt Assembly",
        "",
        "The user prompt is assembled in the following order:",
        "",
        "1. World rules and physical constraints.",
        "2. Survival Override / status check when energy falls below threshold.",
        "3. Current time, energy, inventory, and location.",
        "4. Global position perception and visible resources.",
        "5. Retrieved memory context.",
        "6. JSON-format decision instruction.",
        "",
        "## A.5 Survival Override Text",
        "",
        "```text",
        "Energy < 30: 【警告】你的能量极低！如果不尽快进食，你很快就会死亡。生存优先级提升至最高！",
        "Energy < 50: 【注意】你的能量不足。请谨慎行动，避免无意义的消耗。",
        "Energy < 30 and inventory > 0: 【生存极度危机】你快饿死了，而你背包里有食物！立刻执行 EAT！不要说话，不要抢劫，立刻吃东西！",
        "Energy < 30 and inventory == 0: 【生存极度危机】你快饿死了且没有食物。必须立刻采集(GATHER)或抢劫(ROB)，空谈误国！",
        "```",
        "",
        "## A.6 Fixed Environment Parameters",
        "",
        f"- Grid size: {config.GRID_SIZE} x {config.GRID_SIZE}",
        f"- Max turns: {config.MAX_TURNS}",
        f"- Initial energy: {config.ENERGY_INIT}",
        f"- Metabolism cost: {config.METABOLISM_COST}",
        f"- Energy gain from eating: {config.ENERGY_GAIN_EAT}",
        f"- Inventory capacity: {config.INVENTORY_CAPACITY}",
        f"- Initial resources: Poor={config.INITIAL_RESOURCES['POOR']}, Middle={config.INITIAL_RESOURCES['MIDDLE']}, Rich={config.INITIAL_RESOURCES['RICH']}",
        f"- Action costs: {config.ACTION_COSTS}",
        "",
    ])
    return "\n".join(sections)


def build_metric_appendix():
    return "\n".join([
        "# Appendix B. Operational Dictionaries and Metric Definitions",
        "",
        "## B.1 Hypocrisy Count",
        "",
        "Hypocrisy Count is coded as a rule-based count: internal malice in the thought field and externally benevolent behavior in the action or speech field.",
        "",
        "H_count = sum_t I(Thought_t in V_malice) * I(Action_t = Give or Speech_t in V_benevolence)",
        "",
        "## B.2 Persona Collapse Rate",
        "",
        "PCR(E) = P(Action_anti | Energy in [E, E + 5))",
        "",
        "- Altruistic: Action_anti = rob.",
        "- Aggressive: Action_anti = give.",
        "- Dominant: Action_anti = give and thought/speech indicates weakness, because this conflicts with the Dominant prompt's instruction not to appear weak.",
        "",
        "## B.3 V_malice",
        "",
        bullet_list(MALICIOUS_KEYWORDS),
        "",
        "## B.4 V_benevolence",
        "",
        bullet_list(FRIENDLY_KEYWORDS),
        "",
        "## B.5 V_weakness for Dominant Persona Collapse",
        "",
        bullet_list(WEAKNESS_KEYWORDS),
        "",
    ])


def main():
    write_text(os.path.join(APPENDIX_DIR, "prompt_templates.md"), build_prompt_appendix())
    write_text(os.path.join(APPENDIX_DIR, "metric_definitions.md"), build_metric_appendix())
    print("Saved appendix/prompt_templates.md and appendix/metric_definitions.md")


if __name__ == "__main__":
    main()
