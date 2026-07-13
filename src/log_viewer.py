import json
import os

LOG_FILE = "experiment_log.jsonl"

def parse_log():
    if not os.path.exists(LOG_FILE):
        print(f"❌ File {LOG_FILE} not found!")
        return

    print(f"📖 Opening Story Book: {LOG_FILE}...\n")
    print("="*60)

    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            turn_data = json.loads(line)
            turn = turn_data['turn']
            
            print(f"\n🎬 --- [ TURN {turn} ] --- 🎬")
            
            # 1. 显示每个人的状态和内心戏
            print("\n🧠 [Mental States & Status]")
            for agent in turn_data['agents']:
                name = agent['name']
                energy = agent['status']['energy']
                inv = agent['status']['inventory']
                loc = agent['status']['loc']
                thought = agent['internal']['thought']
                
                # 状态栏
                status_str = f"🔋{energy} 🎒{inv} 📍{loc}"
                if agent['status']['dead']:
                    status_str += " 💀DEAD"
                
                print(f"  👤 {name:<6} | {status_str}")
                print(f"     💭 (心声): {thought}")

                memories = agent.get('memory_dump', 'No memory recorded')
                # 因为 memory_dump 是一个长字符串（用 \n 分隔），我们稍微缩进一下打印
                print(f"     📜 (记忆):")
                for mem_line in memories.split('\n'):
                    if mem_line.strip():
                        print(f"         - {mem_line}")
                # --------------------

                print("-" * 40)

            # 2. 显示实际发生的事件 (动作结果)
            print("\n⚡ [Actions & Events]")
            events = turn_data.get('events', [])
            if not events:
                print("  (Nothing happened)")
            
            for event in events:
                actor = event['agent_name']
                etype = event['type'].upper()
                target = event['target_name'] or ""
                content = event['content']
                success = "✅" if event.get('success', True) else "❌"
                details = event.get('details', '')

                # 格式化输出
                if etype == "TALK":
                    print(f"  🗣️  {actor} 对 {target} 说: \"{content}\"")
                elif etype == "MOVE":
                    print(f"  👣  {actor} 移动到了 {details}")
                elif etype == "GATHER":
                    print(f"  🍄  {actor} 采集: {success} ({details})")
                elif etype == "ROB":
                    res = "抢劫成功! 🎉" if event.get('success') else f"抢劫失败! 💢 ({details})"
                    print(f"  ⚔️  {actor} 袭击了 {target} -> {res}")
                elif etype == "GIVE":
                    print(f"  🎁  {actor} 给了 {target} 物资")
                elif etype == "DEATH":
                    print(f"  💀  {actor} 死亡!")
                elif etype == "SPAWN":
                    print(f"  🌱  环境: 资源刷新了")
                else:
                    print(f"  🔹  {actor} {etype} {target} {success}")

            print("="*60)

if __name__ == "__main__":
    parse_log()