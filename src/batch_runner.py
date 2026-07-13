# batch_runner.py
import simulation
import time
import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT_DIR, "data", "raw_logs")

# --- 实验配置 ---
SCARCITY_LEVELS = ["ABUNDANCE"]

# 3种同质化人格组
PERSONALITY_GROUPS = {
    "All_Aggressive": ["Aggressive", "Aggressive", "Aggressive"],
    "All_Altruistic": ["Altruistic", "Altruistic", "Altruistic"],
    "All_Dominant": ["Dominant", "Dominant", "Dominant"]
}

# --- 测试模式设置 ---
# 🔴 正式跑的时候改成 50 和 50
NUM_RUNS_PER_GROUP = 50   
MAX_TURNS = 50           

def main():
    os.makedirs(LOG_DIR, exist_ok=True)
    total_experiments = len(SCARCITY_LEVELS) * len(PERSONALITY_GROUPS) * NUM_RUNS_PER_GROUP
    count = 0

    print(f"Batch Started. Total: {total_experiments}, Turns: {MAX_TURNS}")

    for scarcity in SCARCITY_LEVELS:
        for p_name, p_list in PERSONALITY_GROUPS.items():
            for i in range(1, NUM_RUNS_PER_GROUP + 1):
                count += 1
                
                # 生成 ID
                run_id = f"{scarcity}_{p_name}_{i:02d}"
                target_log_file = os.path.join(LOG_DIR, f"experiment_{run_id}.jsonl")
                
                # 🔴 核心修改：断点续传检查
                # 如果这个 ID 的日志文件已经存在，且大小不为 0，说明跑过了，跳过
                if os.path.exists(target_log_file) and os.path.getsize(target_log_file) > 0:
                    print(f"[{count}/{total_experiments}] Skipping {run_id} (already done)")
                    continue
                
                # 如果文件不存在，或者为空（上次跑挂了），则开始运行
                print(f"\n[{count}/{total_experiments}] Running {run_id} ...")
                
                try:
                    simulation.run_simulation(
                        run_id=run_id,
                        scarcity_mode=scarcity,
                        personalities=p_list,
                        max_turns=MAX_TURNS
                    )
                except Exception as e:
                    print(f"Error in {run_id}: {e}")
                    # 把错误记录到一个单独的文件，方便你起床看
                    with open(os.path.join(LOG_DIR, "_error_log.txt"), "a") as ef:
                        ef.write(f"{run_id}: {str(e)}\n")
                
                # 🔴 建议：每跑完一次，休息 2-5 秒，保护 API
                time.sleep(2)

if __name__ == "__main__":
    main()