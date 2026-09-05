"""
小苏 MCP 后端（高中生物苏格拉底式伴学）
当前工具：exam_point_card（高考生物考点速记）
后续可按需添加其他生物专用 MCP
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="小苏 MCP · 高中生物伴学")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


# ============ 健康检查 ==========
@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "xiaosu-mcp",
        "endpoints": ["/exam_point_card"],
        "timestamp": datetime.now().isoformat(),
    }


# ============ 工具 1: exam_point_card（高考生物考点速记）============
GAOKAO_DATE = datetime(2027, 6, 7)

# 高中生物核心考点（高中阶段最常考的 6 个，手写，后续可换成知识库动态加载）
EXAM_POINTS = [
    {
        "id": 1,
        "type": "必考",
        "chapter": "必修1 · 第3章 · 细胞呼吸",
        "title": "有氧呼吸三阶段场所",
        "key_concept": "细胞质基质 → 线粒体基质 → 线粒体内膜",
        "key_reaction": "产物:H₂O(第三阶段)、CO₂(第二阶段)",
        "frequency": "近5年12次",
        "tip": "口诀:'膜上有[H]+O₂'——第三阶段在膜上"
    },
    {
        "id": 2,
        "type": "必考",
        "chapter": "必修1 · 第5章 · 光合作用",
        "title": "光反应与暗反应",
        "key_concept": "光反应(类囊体薄膜)→ 暗反应(叶绿体基质)",
        "key_reaction": "[H] 和 ATP 是光反应给暗反应的'红包'",
        "frequency": "近5年10次",
        "tip": "光反应供能供氢,暗反应固定CO₂"
    },
    {
        "id": 3,
        "type": "高频",
        "chapter": "必修1 · 第3章 · 细胞膜",
        "title": "流动镶嵌模型",
        "key_concept": "磷脂双分子层(基本骨架)+ 蛋白质(镶嵌/贯穿/附着)",
        "key_reaction": "糖蛋白(糖被):识别、保护、润滑,只在外侧",
        "frequency": "近5年8次",
        "tip": "特性辨析:流动性 vs 选择透过性(不同概念)"
    },
    {
        "id": 4,
        "type": "必考",
        "chapter": "必修2 · 第1章 · 孟德尔定律",
        "title": "分离定律",
        "key_concept": "等位基因随同源染色体分开而分离",
        "key_reaction": "Aa × Aa → 1AA : 2Aa : 1aa(表现型3:1)",
        "frequency": "近5年15次",
        "tip": "F₂出现3:1的条件:显性完全+配子随机结合+大样本"
    },
    {
        "id": 5,
        "type": "必考",
        "chapter": "必修2 · 第2章 · 减数分裂",
        "title": "8个时期辨析",
        "key_concept": "减Ⅰ(同源分离)+ 减Ⅱ(姐妹分开)",
        "key_reaction": "染色体减半发生在减Ⅰ末期",
        "frequency": "近5年13次",
        "tip": "看图题三看:看同源、看行为、看位置"
    },
    {
        "id": 6,
        "type": "高频",
        "chapter": "必修2 · 第3章 · DNA复制",
        "title": "半保留复制",
        "key_concept": "亲代DNA两条链分别作模板",
        "key_reaction": "复制n次后,含原始链的DNA占 2/2ⁿ",
        "frequency": "近5年9次",
        "tip": "离心实验:轻带(¹⁴N)/中带/重带(¹⁵N)"
    }
]


@app.get("/exam_point_card")
def exam_point_card():
    """高考生物考点速记卡片（供通知公告位轮播用）"""
    today = datetime.now()
    days_left = (GAOKAO_DATE - today).days
    return {
        "code": 200,
        "data": {
            "countdown_days": max(days_left, 0),
            "gaokao_date": GAOKAO_DATE.strftime("%Y-%m-%d"),
            "today_date": today.strftime("%Y-%m-%d"),
            "points": EXAM_POINTS
        }
    }


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
