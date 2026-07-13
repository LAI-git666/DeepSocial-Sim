# world.py
import config
from agent import Agent
from data_types import Event

class World:
    def __init__(self, scarcity_mode=None, agent_personalities=None):
        self.turn = 0
        self.grid = [[0 for _ in range(config.GRID_SIZE)] for _ in range(config.GRID_SIZE)]
        self.agents = []
        
        # 使用传入的模式，若无则用 config 默认值
        self.scarcity_mode = scarcity_mode if scarcity_mode else config.SCARCITY_MODE
        
        # 使用传入的人格列表
        self._init_agents(agent_personalities)

    def _init_agents(self, personalities=None):
        # 定义三个角色的基础属性 (名字, 阶级, 初始物资, 坐标)
        # 注意：物资取自 config.INITIAL_RESOURCES
        roles = [
            ("Kai", "Poor", config.INITIAL_RESOURCES["POOR"], 2, 5),
            ("Elala", "Middle", config.INITIAL_RESOURCES["MIDDLE"], 5, 8),
            ("Jax", "Rich", config.INITIAL_RESOURCES["RICH"], 8, 5)
        ]

        # 如果没有传入 personalities，使用默认混合组 (兼容旧代码)
        if not personalities:
            personalities = ["Aggressive", "Altruistic", "Dominant"]

        # 循环创建 Agent
        for i, (name, cls, inv, x, y) in enumerate(roles):
            # 确保 personalities 长度足够，否则循环取值
            persona = personalities[i % len(personalities)]
            self.agents.append(Agent(name, persona, cls, x, y, config.ENERGY_INIT, inv))

    def get_agent_by_name(self, name):
        for a in self.agents:
            if a.name == name:
                return a
        return None

    def get_all_agent_positions(self):
        """返回全图 GPS 信息 (上帝视角位置)，严禁返回数值状态"""
        return ", ".join([f"{a.name} at ({a.x},{a.y})" for a in self.agents if not a.is_dead])

    def broadcast_events(self, current_turn_events):
        for agent in self.agents:
            if not agent.is_dead:
                agent.perceive(current_turn_events)
                
    def spawn_resources(self):
        # 🔴 修改点 3: 使用 self.scarcity_mode
        if self.scarcity_mode == "ABUNDANCE":
            tx, ty = config.RESOURCE_SPAWN_LOC
            self.grid[tx][ty] += 1
            return Event(self.turn, "spawn", "SYSTEM", location=(tx, ty), content="Food spawned", success=True, importance_score=3)
        return None
    
    def get_visible_resources(self):
        """
        返回地图上所有资源的坐标列表。
        格式: "Food at (5,5), Food at (2,3)"
        """
        resources = []
        for x in range(config.GRID_SIZE):
            for y in range(config.GRID_SIZE):
                amount = self.grid[x][y]
                if amount > 0:
                    resources.append(f"Food({amount}) at ({x},{y})")
        
        if not resources:
            return "No visible food."
        return ", ".join(resources)