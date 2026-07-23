"""
柏拉 v2.0 - 数学工具 MCP 后端
5 个工具：calculator / function_plotter / problem_generator / mistake_recorder / student_profile
单文件部署，适合 Render / Railway / 本地
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import math
import random
import json
import os
from datetime import datetime
from pathlib import Path

app = FastAPI(title="柏拉 v2.0 数学工具 MCP")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)


def sse_format(data: dict) -> str:
    """格式化为 SSE 事件 (data: {...}\\n\\n)"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

# ============ 题库（33+ 道，覆盖函数核心）============
PROBLEM_BANK = {
    "二次函数": [
        {"q": "x² - 5x + 6 = 0，求 x", "a": "x=2 或 x=3", "diff": "mid", "hint": "因式分解"},
        {"q": "x² - 7x + 12 = 0，求 x", "a": "x=3 或 x=4", "diff": "mid", "hint": "因式分解"},
        {"q": "x² - 4x - 5 = 0，求 x", "a": "x=5 或 x=-1", "diff": "mid", "hint": "十字相乘"},
        {"q": "x² - 6x + 9 = 0，求 x", "a": "x=3（重根）", "diff": "mid", "hint": "完全平方"},
        {"q": "y = x² - 4x + 3 的顶点坐标是？", "a": "(2, -1)", "diff": "mid", "hint": "顶点公式"},
        {"q": "y = 2x² - 4x + 1 的最小值", "a": "-1", "diff": "hard", "hint": "配方法"},
        {"q": "抛物线 y = x² - 2x - 3 与 x 轴交点", "a": "(-1, 0) 和 (3, 0)", "diff": "mid", "hint": "y=0 时"},
    ],
    "指数函数": [
        {"q": "2^x = 8，x = ?", "a": "3", "diff": "easy", "hint": "8 = 2^?"},
        {"q": "2^x = 16，x = ?", "a": "4", "diff": "easy", "hint": "16 = 2^?"},
        {"q": "(1/2)^x = 4，x = ?", "a": "-2", "diff": "mid", "hint": "底数小于 1"},
        {"q": "比较 2^0.5 和 2^0.6 的大小", "a": "2^0.5 < 2^0.6", "diff": "mid", "hint": "单调性"},
        {"q": "y = 2^(-x) 和 y = (1/2)^x 是同一函数？", "a": "是", "diff": "mid", "hint": "指数运算法则"},
        {"q": "5^0 = ?", "a": "1", "diff": "easy", "hint": "任何非零数的 0 次方"},
    ],
    "对数函数": [
        {"q": "log₂ 8 = ?", "a": "3", "diff": "easy", "hint": "2^? = 8"},
        {"q": "log₈ 2 = ?", "a": "1/3", "diff": "hard", "hint": "换底公式"},
        {"q": "log(x²) = 2log(x) 恒成立吗？", "a": "仅 x>0 时成立", "diff": "mid", "hint": "对数定义域"},
        {"q": "比较 log₂ 3 和 log₃ 2 的大小", "a": "log₂ 3 > log₃ 2", "diff": "hard", "hint": "换底"},
        {"q": "lg 100 - lg 10 = ?", "a": "1", "diff": "easy", "hint": "对数运算法则"},
        {"q": "ln e² = ?", "a": "2", "diff": "easy", "hint": "自然对数"},
    ],
    "幂函数": [
        {"q": "y = x² 在 (-∞, 0) 上单调？", "a": "递减", "diff": "mid", "hint": "开口朝上的抛物线"},
        {"q": "y = √x 的定义域", "a": "x ≥ 0", "diff": "mid", "hint": "根号下非负"},
        {"q": "比较 0.5² 和 0.5³", "a": "0.5² > 0.5³", "diff": "mid", "hint": "0<a<1 时单调减"},
    ],
    "三角函数": [
        {"q": "sin(π/2) = ?", "a": "1", "diff": "easy", "hint": "特殊角"},
        {"q": "cos(π/3) = ?", "a": "1/2", "diff": "easy", "hint": "特殊角"},
        {"q": "sin(x+π) = ?", "a": "-sin x", "diff": "mid", "hint": "诱导公式"},
        {"q": "y = sin(2x) 的周期", "a": "π", "diff": "mid", "hint": "T = 2π/ω"},
        {"q": "比较 sin(π/6) 和 cos(π/3)", "a": "相等，都 = 1/2", "diff": "mid", "hint": "互余角"},
    ],
    "复合函数": [
        {"q": "y = log(2^x) 的单调性", "a": "单调增", "diff": "hard", "hint": "复合函数单调性"},
        {"q": "y = log(x²+1) 的定义域", "a": "R（全体实数）", "diff": "mid", "hint": "x²+1 > 0 恒成立"},
        {"q": "y = 2^(x²) 的单调性", "a": "x<0 减；x>0 增", "diff": "hard", "hint": "复合函数"},
        {"q": "y = √(1-x²) 的值域", "a": "[0, 1]", "diff": "hard", "hint": "1-x² ≥ 0"},
    ],
}

# ============ 错题存储（JSON 文件）============
MISTAKES_DB = "mistakes.json"
MISTAKES = []


def load_mistakes():
    global MISTAKES
    if os.path.exists(MISTAKES_DB):
        try:
            with open(MISTAKES_DB, "r", encoding="utf-8") as f:
                MISTAKES = json.load(f)
        except Exception:
            MISTAKES = []


def save_mistakes():
    try:
        with open(MISTAKES_DB, "w", encoding="utf-8") as f:
            json.dump(MISTAKES, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


load_mistakes()


# ============ 学生画像存储（JSON 文件）============
PROFILES_DB = "student_profiles.json"
PROFILES = []


def load_profiles():
    global PROFILES
    if os.path.exists(PROFILES_DB):
        try:
            with open(PROFILES_DB, "r", encoding="utf-8") as f:
                PROFILES = json.load(f)
        except Exception:
            PROFILES = []


def save_profiles():
    try:
        with open(PROFILES_DB, "w", encoding="utf-8") as f:
            json.dump(PROFILES, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


load_profiles()


# ============ 健康检查 ==========
@app.get("/")
def health():
    return {
        "status": "ok",
        "service": "balla-v2-mcp",
        "endpoints": [
            "/calculator",
            "/function_plotter",
            "/problem_generator",
            "/mistake_recorder",
            "/student_profile",
        ],
        "topics": list(PROBLEM_BANK.keys()),
        "total_mistakes": len(MISTAKES),
        "total_profiles": len(PROFILES),
        "timestamp": datetime.now().isoformat(),
    }


# ============ 工具 1: calculator ==========
@app.get("/calculator")
async def calculator(expr: str = "1+1"):
    """计算数学表达式 - SSE 格式"""
    async def event_stream():
        try:
            safe_dict = {
                "__builtins__": {},
                "math": math,
                "sqrt": math.sqrt,
                "log": math.log,
                "log2": math.log2,
                "log10": math.log10,
                "ln": math.log,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "pi": math.pi,
                "e": math.e,
                "abs": abs,
                "round": round,
                "pow": pow,
            }
            result = eval(expr, safe_dict)
            formatted = f"{expr} = {result:.6f}".rstrip("0").rstrip(".") if isinstance(result, float) else f"{expr} = {result}"
            yield sse_format({
                "status": "ok",
                "input": expr,
                "result": str(result),
                "formatted": formatted,
            })
        except Exception as ex:
            yield sse_format({"status": "error", "input": expr, "error": str(ex)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ============ 工具 2: function_plotter ==========
@app.get("/function_plotter")
async def plotter(func: str = "x*x", x_min: float = -5, x_max: float = 5):
    """生成函数图像数据 - SSE 格式"""
    async def event_stream():
        try:
            safe_dict = {"__builtins__": {}, "math": math, "x": 0}
            data = []
            for i in range(101):
                x = x_min + (x_max - x_min) * i / 100
                safe_dict["x"] = x
                try:
                    y = eval(func, safe_dict)
                    data.append({"x": round(x, 2), "y": round(y, 4) if abs(y) < 100 else None})
                except Exception:
                    data.append({"x": round(x, 2), "y": None})

            # 零点检测
            zeros = []
            for i in range(len(data) - 1):
                if data[i]["y"] is not None and data[i + 1]["y"] is not None:
                    if (data[i]["y"] > 0 > data[i + 1]["y"]) or (data[i]["y"] < 0 < data[i + 1]["y"]):
                        zeros.append(round((data[i]["x"] + data[i + 1]["x"]) / 2, 2))

            # 趋势
            valid = [d["y"] for d in data if d["y"] is not None]
            trend = "递增" if valid[-1] > valid[0] else "递减"

            yield sse_format({
                "status": "ok",
                "function": func,
                "x_range": [x_min, x_max],
                "trend": trend,
                "zeros": zeros[:5],
                "data_sample": data[::10],
                "description": f"y = {func} 在 [{x_min}, {x_max}] 上{trend}，零点约在 {zeros[:3] if zeros else '无'}",
            })
        except Exception as ex:
            yield sse_format({"status": "error", "error": str(ex)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ============ 工具 3: problem_generator ==========
@app.get("/problem_generator")
async def problem_gen(topic: str = "二次函数", difficulty: str = "mid"):
    """生成同类题 - SSE 格式"""
    async def event_stream():
        try:
            bank = PROBLEM_BANK.get(topic, PROBLEM_BANK["二次函数"])
            filtered = [p for p in bank if p.get("diff") == difficulty] or bank
            problem = random.choice(filtered)
            yield sse_format({
                "status": "ok",
                "topic": topic,
                "difficulty": difficulty,
                "question": problem["q"],
                "answer": problem["a"],
                "hint": problem.get("hint", ""),
                "柏拉提示": "（答案仅柏拉可见，不要直接告诉学生）",
            })
        except Exception as ex:
            yield sse_format({"status": "error", "error": str(ex)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/problem_generator/topics")
def list_topics():
    """列出所有可用主题"""
    return {
        "topics": [
            {"name": k, "count": len(v), "difficulties": list(set(p.get("diff", "mid") for p in v))}
            for k, v in PROBLEM_BANK.items()
        ]
    }


# ============ 工具 4: mistake_recorder ==========
@app.get("/mistake_recorder")
async def record_or_list_mistakes(
    action: str = "list",
    student_id: str = "stu_001",
    function_type: str = "未分类",
    question: str = "",
    wrong_answer: str = "",
    correct_answer: str = "",
    error_type: str = "未分类",
):
    """错题记录工具 - SSE 格式"""
    async def event_stream():
        global MISTAKES

        if action == "record":
            entry = {
                "id": len(MISTAKES) + 1,
                "student_id": student_id,
                "function_type": function_type,
                "question": question,
                "wrong_answer": wrong_answer,
                "correct_answer": correct_answer,
                "error_type": error_type,
                "created_at": datetime.now().isoformat(),
            }
            MISTAKES.append(entry)
            save_mistakes()
            yield sse_format({
                "status": "ok",
                "action": "recorded",
                "id": entry["id"],
                "total_mistakes": len(MISTAKES),
                "entry": entry,
            })

        elif action == "list":
            filtered = [m for m in MISTAKES if m["student_id"] == student_id]
            by_type = {}
            for m in filtered:
                et = m.get("error_type", "未分类")
                by_type[et] = by_type.get(et, 0) + 1
            yield sse_format({
                "status": "ok",
                "action": "list",
                "student_id": student_id,
                "count": len(filtered),
                "by_error_type": by_type,
                "mistakes": filtered[-10:],
            })

        elif action == "stats":
            filtered = [m for m in MISTAKES if m["student_id"] == student_id]
            by_type = {}
            by_func = {}
            for m in filtered:
                et = m.get("error_type", "未分类")
                ft = m.get("function_type", "未分类")
                by_type[et] = by_type.get(et, 0) + 1
                by_func[ft] = by_func.get(ft, 0) + 1
            yield sse_format({
                "status": "ok",
                "action": "stats",
                "student_id": student_id,
                "total": len(filtered),
                "by_error_type": by_type,
                "by_function_type": by_func,
            })
        else:
            yield sse_format({"status": "error", "error": f"unknown action: {action}"})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.delete("/mistake_recorder")
def clear_mistakes(student_id: str = None):
    """清空错题（用于测试）"""
    global MISTAKES
    if student_id:
        MISTAKES = [m for m in MISTAKES if m["student_id"] != student_id]
    else:
        MISTAKES = []
    save_mistakes()
    return {"status": "ok", "remaining": len(MISTAKES)}


# ============ 工具 5: student_profile（学情画像 - 长期记忆核心）============
@app.get("/student_profile")
async def student_profile(
    action: str = "read",
    name: str = "",
    grade: str = "",
    learning_style: str = "",
    metacognition_level: str = "",
    weak_points: str = "",
    last_topic: str = "",
    session_count: int = 0,
    notes: str = "",
    keyword: str = "",
):
    """学生学情画像 - SSE 格式

    Actions:
        - read: 按姓名查档案（查不到返回found:false）
        - create: 新建档案（如重名返回status:duplicate）
        - update: 更新档案某字段
        - search: 关键词模糊搜索
        - list: 列出所有档案
    """
    async def event_stream():
        global PROFILES

        if action == "read":
            # 按姓名精确查
            matches = [p for p in PROFILES if p.get("name") == name]
            if not matches:
                yield sse_format({
                    "status": "ok",
                    "action": "read",
                    "found": False,
                    "name": name,
                    "message": f"未找到名为「{name}」的档案"
                })
            elif len(matches) == 1:
                yield sse_format({
                    "status": "ok",
                    "action": "read",
                    "found": True,
                    "name": name,
                    "profile": matches[0]
                })
            else:
                # 多个同名（理论上不该出现，但兜底）
                yield sse_format({
                    "status": "ok",
                    "action": "read",
                    "found": "multiple",
                    "name": name,
                    "count": len(matches),
                    "profiles": matches
                })

        elif action == "create":
            # 先查重名
            existing = [p for p in PROFILES if p.get("name") == name]
            if existing:
                yield sse_format({
                    "status": "duplicate",
                    "action": "create",
                    "name": name,
                    "existing_count": len(existing),
                    "message": f"已经有一个叫「{name}」的档案了～换个名字？比如「{name}²」、「函数小王子{name}」都行。",
                    "hint": "请用新的 name 再调一次 create"
                })
                return
            # 正常创建
            new_profile = {
                "name": name,
                "grade": grade or "未告知",
                "learning_style": learning_style or "未告知",
                "metacognition_level": metacognition_level or "未告知",
                "weak_points": weak_points or "",
                "last_topic": last_topic or "",
                "session_count": session_count or 0,
                "notes": notes or "",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            PROFILES.append(new_profile)
            save_profiles()
            yield sse_format({
                "status": "ok",
                "action": "created",
                "profile": new_profile,
                "total_profiles": len(PROFILES)
            })

        elif action == "update":
            # 按姓名找
            found = [p for p in PROFILES if p.get("name") == name]
            if not found:
                yield sse_format({
                    "status": "error",
                    "action": "update",
                    "error": f"未找到名为「{name}」的档案，无法更新"
                })
                return
            profile = found[0]
            # 只更新非空字段
            if grade: profile["grade"] = grade
            if learning_style: profile["learning_style"] = learning_style
            if metacognition_level: profile["metacognition_level"] = metacognition_level
            if weak_points: profile["weak_points"] = weak_points
            if last_topic: profile["last_topic"] = last_topic
            if session_count: profile["session_count"] = session_count
            if notes: profile["notes"] = notes
            profile["updated_at"] = datetime.now().isoformat()
            save_profiles()
            yield sse_format({
                "status": "ok",
                "action": "updated",
                "profile": profile
            })

        elif action == "search":
            # 关键词搜索（姓名/薄弱点/上次学到）
            kw = keyword or notes
            if not kw:
                yield sse_format({
                    "status": "error",
                    "action": "search",
                    "error": "缺少 keyword 参数"
                })
                return
            results = [p for p in PROFILES if
                       kw in p.get("name", "") or
                       kw in p.get("weak_points", "") or
                       kw in p.get("last_topic", "")]
            yield sse_format({
                "status": "ok",
                "action": "search",
                "keyword": kw,
                "count": len(results),
                "results": results
            })

        elif action == "list":
            yield sse_format({
                "status": "ok",
                "action": "list",
                "count": len(PROFILES),
                "profiles": PROFILES
            })

        elif action == "delete":
            # 删除档案（测试用）
            before = len(PROFILES)
            PROFILES[:] = [p for p in PROFILES if p.get("name") != name]
            save_profiles()
            yield sse_format({
                "status": "ok",
                "action": "deleted",
                "name": name,
                "removed": before - len(PROFILES),
                "remaining": len(PROFILES)
            })

        else:
            yield sse_format({"status": "error", "error": f"unknown action: {action}"})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


if __name__ == "__main__":
    # 把 tools 目录挂到 /tools 路径下，4 个工具都能访问
    tools_dir = Path(__file__).parent / "tools"
    if not tools_dir.exists():
        tools_dir = Path(__file__).parent.parent / "柏拉v2.0_工具页面"

    if tools_dir.exists():
        app.mount("/tools", StaticFiles(directory=str(tools_dir), html=True), name="tools")
        print(f"✅ 静态工具已挂载: {tools_dir}")
        print(f"   📂 Hub: http://localhost:8000/tools/index.html")
        print(f"   🧮 计算器: http://localhost:8000/tools/calculator.html")
        print(f"   📈 画图: http://localhost:8000/tools/function_plotter.html")
        print(f"   📝 同类题: http://localhost:8000/tools/problem_generator.html")
        print(f"   📒 错题本: http://localhost:8000/tools/mistake_notebook.html")
    else:
        print(f"⚠️  工具目录未找到: {tools_dir}")
        print(f"   请把 4 个 HTML 放到 {tools_dir}")

    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
