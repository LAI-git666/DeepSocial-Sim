# agent.py
from memory import MemoryStream
import prompts
from llm_client import LLMClient

client = None


def get_client():
    global client
    if client is None:
        client = LLMClient()
    return client

class Agent:
    def __init__(self, name, personality, social_class, x, y, energy, inventory):
        self.name = name
        self.personality = personality
        self.social_class = social_class
        self.x = x
        self.y = y
        self.energy = energy
        self.inventory = inventory
        self.is_dead = False
        self.memory = MemoryStream(self.name)

    def perceive(self, events):
        """接收世界广播"""
        for event in events:
            self.memory.add_event_from_broadcast(event)

    def think_and_act(self, world):
        """核心思考函数"""
        if self.is_dead:
            return {"action": "idle"}

        # 1. 获取上下文
        gps_info = world.get_all_agent_positions()

         # 🔴 新增：获取资源信息
        resource_info = world.get_visible_resources()
        
        memory_text = self.memory.retrieve() 
        time_info = f"Turn {world.turn}"
        
        # --- 修改点：移除 limit 参数 ---
        memory_text = self.memory.retrieve() 
        
        time_info = f"Turn {world.turn}"
        
        # 2. 构建 Prompt
        sys_p = prompts.PERSONALITY_PROMPTS.get(self.personality, "You are a survivor.")
        sys_p = sys_p.format(name=self.name)
        
         # 🔴 修改：传入 resource_info
        user_p = prompts.get_user_prompt(self, gps_info, resource_info, memory_text, time_info)
        
        # 3. 调用 API
        return get_client().get_response(sys_p, user_p)