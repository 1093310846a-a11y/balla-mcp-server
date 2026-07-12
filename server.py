"""
柏拉 v2.0 MCP 工具 SSE 服务
4 个端点：calculator / function_plotter / problem_generator / mistake_recorder
"""

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import math
import json
import os
import random
from datetime import datetime

app = FastAPI(title="柏拉 v2.0 MCP 工具服务")

# 允许跨域（超星平台调用需要）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def sse_format(data: dict) -> str:
    """格式化为 SSE 事件"""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# ========== 工具 1：calculator（计算器）==========
@app.get("/calculator")
async def calculator(expr: str = "1+1"):
    """计算数学表达式"""
    async def event_stream():
        try:
            # 安全计算（限制可用的函数）
            safe_dict = {
                "__builtins__": {},
                "math": math,
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
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
            }
            result = eval(expr, safe_dict)

            # 发送结果
            yield sse_format({
                "type": "calculator_result",
                "input": expr,
                "result": result,
                "formatted": f"→ {result:.6f}".rstrip("0").rstrip(".") if isinstance(result, float) else f"→ {result}",
                "status": "success"
            })
        except Exception as ex:
            yield sse_format({
                "type": "calculator_result",
                "input": expr,
                "error": str(ex),
                "status": "error"
            })

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ========== 工具 2：function_plotter（函数画图）==========
@app.get("/function_plotter")
async def function_plotter(func: str = "2**x", x_min: float = -5, x_max: float = 5):
    """生成函数图像数据（返回文字描述 + 关键点）"""
    async def event_stream():
        try:
            safe_dict = {
                "__builtins__": {},
                "math": math,
                "x": 0,  # 占位
            }

            xs, ys = [], []
            for i in range(101):
                x = x_min + (x_max - x_min) * i / 100
                safe_dict["x"] = x
                try:
                    y = eval(func, safe_dict)
                    if math.isfinite(y) and abs(y) < 100:
                        xs.append(round(x, 2))
                        ys.append(round(y, 4))
                    else:
                        xs.append(round(x, 2))
                        ys.append(None)
                except:
                    xs.append(round(x, 2))
                    ys.append(None)

            # 检测关键点
            zeros = []
            for i in range(len(ys) - 1):
                if ys[i] is not None and ys[i+1] is not None:
                    if (ys[i] > 0 and ys[i+1] < 0) or (ys[i] < 0 and ys[i+1] > 0) or ys[i] == 0:
                        zeros.append(round((xs[i] + xs[i+1]) / 2, 2))

            # 检测趋势
            valid_ys = [y for y in ys if y is not None]
            if len(valid_ys) >= 2:
                trend = "增" if valid_ys[-1] > valid_ys[0] else "减"
            else:
                trend = "未知"

            # 描述
            description = f"y = {func} 在 [{x_min}, {x_max}] 范围内"
            description += f"，整体趋势{trend}"
            if zeros:
                description += f"，零点约在 {zeros[:3]}"
            description += "。"

            yield sse_format({
                "type": "plotter_result",
                "func": func,
                "x_range": [x_min, x_max],
                "data_points": list(zip(xs[::5], [y if y is not None else 0 for y in ys[::5]])),  # 抽样
                "zeros": zeros[:5],
                "trend": trend,
                "description": description,
                "status": "success"
            })
        except Exception as ex:
            yield sse_format({
                "type": "plotter_result",
                "func": func,
                "error": str(ex),
                "status": "error"
            })

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ========== 工具 3：problem_generator（同类题生成）==========
PROBLEM_TEMPLATES = {
    "exp": [
        ("2^x = 8，求 x", "x=3"),
        ("2^x = 16，求 x", "x=4"),
        ("(1/2)^x = 4，求 x", "x=-2"),
        ("比较 2^0.5 和 2^0.6 的大小", "2^0.5 < 2^0.6"),
        ("y=2^(-x) 和 y=(1/2)^x 是不是同一函数？", "是"),
    ],
    "log": [
        ("log_2 8 = ?", "3"),
        ("log_8 2 = ?", "1/3"),
        ("log(x²) = 2log(x) 恒成立吗？", "仅 x>0 时成立"),
        ("比较 log_2 3 和 log_3 2 的大小", "log_2 3 > log_3 2"),
        ("lg 100 - lg 10 = ?", "1"),
    ],
    "quad": [
        ("x² - 5x + 6 = 0，求 x", "x=2 或 x=3"),
        ("x² - 7x + 12 = 0，求 x", "x=3 或 x=4"),
        ("x² - 4x - 5 = 0，求 x", "x=5 或 x=-1"),
        ("x² - 6x + 9 = 0，求 x", "x=3"),
        ("y=x²-4x+3 的顶点坐标", "(2, -1)"),
    ],
    "trig": [
        ("sin(π/2) = ?", "1"),
        ("cos(π/3) = ?", "1/2"),
        ("sin(x+π) = ?", "-sin x"),
        ("y=sin(2x) 的周期", "π"),
        ("比较 sin(π/6) 和 cos(π/3)", "都等于 1/2"),
    ],
    "compose": [
        ("y=log(2^x) 的单调性", "单调增"),
        ("y=log(x²+1) 的定义域", "R"),
        ("y=2^(x²) 的单调性", "x<0 减；x>0 增"),
        ("y=sin(2x+π/3) 的单调区间", "[-π/3, π/6]"),
        ("y=√(1-x²) 的值域", "[0, 1]"),
    ]
}

@app.get("/problem_generator")
async def problem_generator(topic: str = "quad", difficulty: str = "mid"):
    """生成同类题"""
    async def event_stream():
        try:
            problems = PROBLEM_TEMPLATES.get(topic, PROBLEM_TEMPLATES["quad"])
            problem, answer = random.choice(problems)

            yield sse_format({
                "type": "problem_result",
                "topic": topic,
                "difficulty": difficulty,
                "question": problem,
                "answer": answer,
                "status": "success"
            })
        except Exception as ex:
            yield sse_format({
                "type": "problem_result",
                "error": str(ex),
                "status": "error"
            })

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ========== 工具 4：mistake_recorder（错题归档）==========
# 用内存存储（生产环境应该用数据库）
mistake_log = []

@app.get("/mistake_recorder")
async def mistake_recorder(
    student_id: str = "stu_001",
    function_type: str = "对数函数",
    question: str = "log(x²)=2log(x) 恒成立吗？",
    wrong_answer: str = "恒成立",
    correct_answer: str = "仅 x>0 时成立",
    error_type: str = "对数运算法则"
):
    """记录错题"""
    async def event_stream():
        try:
            entry = {
                "id": f"m_{len(mistake_log) + 1:03d}",
                "student_id": student_id,
                "function_type": function_type,
                "question": question,
                "wrong_answer": wrong_answer,
                "correct_answer": correct_answer,
                "error_type": error_type,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "resolved": False
            }
            mistake_log.append(entry)

            yield sse_format({
                "type": "mistake_recorded",
                "entry": entry,
                "total_mistakes": len(mistake_log),
                "status": "success"
            })
        except Exception as ex:
            yield sse_format({
                "type": "mistake_error",
                "error": str(ex),
                "status": "error"
            })

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/mistake_recorder/list")
async def list_mistakes(student_id: str = "stu_001"):
    """列出学生所有错题"""
    async def event_stream():
        try:
            student_mistakes = [m for m in mistake_log if m["student_id"] == student_id]
            yield sse_format({
                "type": "mistake_list",
                "student_id": student_id,
                "count": len(student_mistakes),
                "mistakes": student_mistakes,
                "status": "success"
            })
        except Exception as ex:
            yield sse_format({
                "type": "mistake_error",
                "error": str(ex),
                "status": "error"
            })

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ========== 健康检查 ==========
@app.get("/")
async def health():
    return {"status": "ok", "service": "balla-v2-mcp", "endpoints": ["/calculator", "/function_plotter", "/problem_generator", "/mistake_recorder"]}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
