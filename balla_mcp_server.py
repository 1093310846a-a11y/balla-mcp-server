"""
小苏 MCP 后端（高中生物苏格拉底式伴学）
工具：daily_panel（高中生物伴学面板）
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
        "endpoints": ["/daily_panel"],
        "timestamp": datetime.now().isoformat(),
    }


# ============ 高考日期 ============
GAOKAO_DATE = datetime(2027, 6, 7)


# ============ 6 个核心考点（必修 1+2 最常考）============
EXAM_POINTS = [
    {
        "id": 1, "type": "必考",
        "chapter": "必修1 · 细胞呼吸",
        "title": "有氧呼吸三阶段场所",
        "key_concept": "细胞质基质→线粒体基质→线粒体内膜",
        "frequency": "近5年12次",
    },
    {
        "id": 2, "type": "必考",
        "chapter": "必修1 · 光合作用",
        "title": "光反应与暗反应",
        "key_concept": "光反应(类囊体)→暗反应(基质)",
        "frequency": "近5年10次",
    },
    {
        "id": 3, "type": "必考",
        "chapter": "必修2 · 孟德尔定律",
        "title": "分离定律",
        "key_concept": "Aa×Aa → 1AA:2Aa:1aa",
        "frequency": "近5年15次",
    },
    {
        "id": 4, "type": "必考",
        "chapter": "必修2 · 减数分裂",
        "title": "8个时期辨析",
        "key_concept": "减Ⅰ同源分离+减Ⅱ姐妹分开",
        "frequency": "近5年13次",
    },
    {
        "id": 5, "type": "高频",
        "chapter": "必修1 · 细胞膜",
        "title": "流动镶嵌模型",
        "key_concept": "磷脂双分子层+蛋白质",
        "frequency": "近5年8次",
    },
    {
        "id": 6, "type": "高频",
        "chapter": "必修2 · DNA复制",
        "title": "半保留复制",
        "key_concept": "复制n次后原始链占2/2ⁿ",
        "frequency": "近5年9次",
    },
]


# ============ 5 个功能入口（对应 5 个 Agent）============
FEATURE_ENTRIES = [
    {"id": 1, "icon": "🎯", "name": "纠错家教", "desc": "苏格拉底7步引导", "color": "#2EBE9D"},
    {"id": 2, "icon": "🔬", "name": "错题分析", "desc": "错因雷达+变式题", "color": "#FF6B35"},
    {"id": 3, "icon": "📚", "name": "预习助手", "desc": "5题诊断+听课建议", "color": "#5B8DEF"},
    {"id": 4, "icon": "🔁", "name": "复习规划", "desc": "艾宾浩斯Day0-Day14", "color": "#A66DD4"},
    {"id": 5, "icon": "💬", "name": "心情树洞", "desc": "考前安心包+冷知识", "color": "#F5B82E"},
]


# ============ 12 条生物冷知识（按日期切换）============
BIO_TIPS = [
    {"title": "海马爸爸会怀孕", "content": "雄性海马腹部有育儿袋,受精卵在里面孵化,是动物界少见的'父爱'现象。"},
    {"title": "章鱼有三个心脏", "content": "两个负责给鳃供血,一个给全身供血。游泳时主心脏会停跳,所以章鱼更爱爬行。"},
    {"title": "你的DNA够往返太阳", "content": "体内所有细胞DNA首尾相连,长度约340亿公里,可从地球到太阳再返回。"},
    {"title": "植物会做算术", "content": "捕蝇草5秒内被触两次才闭合,这样能避免雨滴误触浪费能量。"},
    {"title": "人类有860亿脑细胞", "content": "比银河系恒星还多,但日常仅调用约10%,潜力远未开发。"},
    {"title": "细菌会交换基因", "content": "细菌通过'接合'传递质粒,这是抗生素耐药性快速扩散的根源。"},
    {"title": "心脏每天跳10万次", "content": "按平均寿命算,一生约跳25亿次,堪比一部永不停歇的泵。"},
    {"title": "植物也有神经", "content": "含羞草受触会'传电',信号传播速度可达每秒5毫米。"},
    {"title": "病毒不算生命", "content": "病毒无细胞结构,不能独立代谢,只能寄生在活细胞内复制。"},
    {"title": "人和香蕉共享50%基因", "content": "所有生物源于共同祖先,人与果蝇共享60%、与老鼠共享85%DNA。"},
    {"title": "蓝光会伤眼", "content": "电子屏幕的短波蓝光会引起视网膜氧化应激,夜间使用影响睡眠。"},
    {"title": "血型不只ABO", "content": "人类已知血型系统超43种(ABO、Rh、MNS、Kell…),ABO只是最常见。"},
]


# ============ 学习鼓励语（按日期切换）============
MOTIVATIONS = [
    "今天弄懂一个小点,比昨天更厉害一点。",
    "错的题,都是下次拿分的题。",
    "高考看的是谁笑到最后,不是谁笑到最响。",
    "课本翻三遍,胜过刷题三十道。",
    "睡前回忆一遍今天学的,记忆留存率提升50%。",
    "错题不丢人,丢人的是同一道错两次。",
    "苏格拉底说:我唯一知道的,就是我一无所知。所以要一直问。",
    "生物不难,难的只是还没搞懂的'为什么'。",
]


# ============ 主端点：高中生物伴学面板 ============
@app.get("/daily_panel")
def daily_panel():
    """高中生物伴学面板（通知公告位 iframe 嵌入用）"""
    today = datetime.now()
    days_left = (GAOKAO_DATE - today).days
    weekday_cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][today.weekday()]

    # 用"年内第几天"做稳定 hash,保证同一日期下推荐内容不跳
    day_index = today.timetuple().tm_yday

    return {
        "code": 200,
        "data": {
            # 基础信息
            "countdown_days": max(days_left, 0),
            "today_date": today.strftime("%Y年%m月%d日"),
            "weekday": weekday_cn,

            # 学习数据（MVP 版,后续接 student_profile MCP）
            "study_stats": {
                "consecutive_days": 7,
                "this_week_chapters": 3,
                "this_week_mistakes": 12,
                "mastery_rate": 78,
            },

            # 6 个核心考点
            "exam_points": EXAM_POINTS,

            # 5 个功能入口
            "feature_entries": FEATURE_ENTRIES,

            # 今日冷知识（按日切换）
            "daily_tip": BIO_TIPS[day_index % len(BIO_TIPS)],

            # 鼓励语（按日切换）
            "motivation": MOTIVATIONS[day_index % len(MOTIVATIONS)],
        }
    }


if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
