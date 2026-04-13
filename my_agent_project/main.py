"""
三省六部多智能体系统 - main.py
基于 LangGraph 的工作流流转
GPT仅用于：门下省(逻辑)
Kimi用于：御史台(长上下文终审)
Qwen用于：其他所有节点 (API v2 + 思考模式)
"""

import os
from dotenv import load_dotenv
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from openai import OpenAI

# 加载环境变量
load_dotenv()

# ============ 初始化模型客户端 ============

# OpenAI GPT (仅用于门下省)
gpt_client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE")
)

# MiniMax (吏部用)
minimax_client = OpenAI(
    api_key=os.getenv("MINIMAX_API_KEY"),
    base_url=os.getenv("MINIMAX_API_BASE")
)

# Qwen (主力 - API v2)
qwen_client = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url=os.getenv("QWEN_API_BASE")
)

# Kimi (御史台用)
kimi_client = OpenAI(
    api_key=os.getenv("KIMI_API_KEY"),
    base_url=os.getenv("KIMI_API_BASE")
)

# 模型名称
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4o")
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "MiniMax-Text-01")
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen3.6-plus")
KIMI_MODEL = os.getenv("KIMI_MODEL", "moonshotai/kimi-k2.5")

# ============ 统一调用接口 ============

def call_gpt(prompt: str) -> str:
    """GPT调用"""
    response = gpt_client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def call_minimax(prompt: str) -> str:
    """MiniMax调用"""
    response = minimax_client.chat.completions.create(
        model=MINIMAX_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def call_qwen(prompt: str, thinking: bool = True) -> str:
    """Qwen调用 - API v2 + 思考模式"""
    response = qwen_client.responses.create(
        model=QWEN_MODEL,
        input=prompt,
        extra_body={"enable_thinking": thinking}
    )

    result = ""
    for item in response.output:
        if item.type == "reasoning":
            for summary in item.summary:
                result += f"【推理过程】\n{summary.text[:500]}\n\n"
        elif item.type == "message":
            result += f"【最终答案】\n{item.content[0].text}"
    return result

def call_kimi(prompt: str) -> str:
    """Kimi调用"""
    payload = {
        "model": KIMI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 16384,
        "temperature": 1.0,
        "top_p": 1.0,
        "chat_template_kwargs": {"thinking": True}
    }

    import requests
    headers = {
        "Authorization": f"Bearer {os.getenv('KIMI_API_KEY')}",
        "Accept": "application/json"
    }

    response = requests.post(
        f"{os.getenv('KIMI_API_BASE')}/chat/completions",
        headers=headers,
        json=payload
    )
    return response.json()["choices"][0]["message"]["content"]

# ============ 状态定义 ============

class AgentState(TypedDict):
    task: str
    zhong_shu_draft: str
    men_xia_review: str
    shang_shu_plan: str
    li_bu_opinion: str
    hu_bu_opinion: str
    li_yi_bu_opinion: str
    bing_bu_opinion: str
    xing_bu_opinion: str
    gong_bu_opinion: str
    yu_shi_tai_ruling: str
    current_phase: str
    messages: Annotated[list, ...]

# ============ 节点函数 ============

def zhong_shu_sheng_node(state: AgentState) -> AgentState:
    """中书省：起草 (Qwen)"""
    from prompts import ZHONG_SHU_SHENG_PROMPT
    prompt = f"{ZHONG_SHU_SHENG_PROMPT}\n\n【圣意】\n{state['task']}"
    result = call_qwen(prompt)
    return {
        **state,
        "zhong_shu_draft": result,
        "current_phase": "中书省-草案完成",
        "messages": state["messages"] + [("中书省", result)]
    }

def men_xia_sheng_node(state: AgentState) -> AgentState:
    """门下省：审议 (GPT)"""
    from prompts import MEN_XIA_SHENG_PROMPT
    prompt = f"{MEN_XIA_SHENG_PROMPT}\n\n【中书省草案】\n{state['zhong_shu_draft']}"
    result = call_gpt(prompt)
    return {
        **state,
        "men_xia_review": result,
        "current_phase": "门下省-审议完成",
        "messages": state["messages"] + [("门下省", result)]
    }

def shang_shu_sheng_node(state: AgentState) -> AgentState:
    """尚书省：执行分案 (Qwen)"""
    from prompts import SHANG_SHU_SHENG_PROMPT
    prompt = f"{SHANG_SHU_SHENG_PROMPT}\n\n【门下省审议结果】\n{state['men_xia_review']}"
    result = call_qwen(prompt)
    return {
        **state,
        "shang_shu_plan": result,
        "current_phase": "尚书省-分案完成",
        "messages": state["messages"] + [("尚书省", result)]
    }

def li_bu_node(state: AgentState) -> AgentState:
    """吏部：分工 (MiniMax)"""
    from prompts import LI_BU_PROMPT
    prompt = f"{LI_BU_PROMPT}\n\n【尚书省执行分案】\n{state['shang_shu_plan']}"
    result = call_minimax(prompt)
    return {
        **state,
        "li_bu_opinion": result,
        "current_phase": "吏部-会办完成",
        "messages": state["messages"] + [("吏部", result)]
    }

def hu_bu_node(state: AgentState) -> AgentState:
    """户部：资源 (Qwen)"""
    from prompts import HU_BU_PROMPT
    prompt = f"{HU_BU_PROMPT}\n\n【尚书省执行分案】\n{state['shang_shu_plan']}"
    result = call_qwen(prompt)
    return {
        **state,
        "hu_bu_opinion": result,
        "current_phase": "户部-会办完成",
        "messages": state["messages"] + [("户部", result)]
    }

def li_yi_bu_node(state: AgentState) -> AgentState:
    """礼部：表达 (Qwen)"""
    from prompts import LI_YI_BU_PROMPT
    prompt = f"{LI_YI_BU_PROMPT}\n\n【尚书省执行分案】\n{state['shang_shu_plan']}"
    result = call_qwen(prompt)
    return {
        **state,
        "li_yi_bu_opinion": result,
        "current_phase": "礼部-会办完成",
        "messages": state["messages"] + [("礼部", result)]
    }

def bing_bu_node(state: AgentState) -> AgentState:
    """兵部：推进 (Qwen)"""
    from prompts import BING_BU_PROMPT
    prompt = f"{BING_BU_PROMPT}\n\n【尚书省执行分案】\n{state['shang_shu_plan']}"
    result = call_qwen(prompt)
    return {
        **state,
        "bing_bu_opinion": result,
        "current_phase": "兵部-会办完成",
        "messages": state["messages"] + [("兵部", result)]
    }

def xing_bu_node(state: AgentState) -> AgentState:
    """刑部：风险 (Qwen)"""
    from prompts import XING_BU_PROMPT
    prompt = f"{XING_BU_PROMPT}\n\n【尚书省执行分案】\n{state['shang_shu_plan']}"
    result = call_qwen(prompt)
    return {
        **state,
        "xing_bu_opinion": result,
        "current_phase": "刑部-会办完成",
        "messages": state["messages"] + [("刑部", result)]
    }

def gong_bu_node(state: AgentState) -> AgentState:
    """工部：技术 (Qwen)"""
    from prompts import GONG_BU_PROMPT
    prompt = f"{GONG_BU_PROMPT}\n\n【尚书省执行分案】\n{state['shang_shu_plan']}"
    result = call_qwen(prompt)
    return {
        **state,
        "gong_bu_opinion": result,
        "current_phase": "工部-会办完成",
        "messages": state["messages"] + [("工部", result)]
    }

def yu_shi_tai_node(state: AgentState) -> AgentState:
    """御史台：裁决 (Kimi)"""
    from prompts import YU_SHI_TAI_PROMPT
    six_bu = f"""【吏部意见】
{state['li_bu_opinion']}

【户部意见】
{state['hu_bu_opinion']}

【礼部意见】
{state['li_yi_bu_opinion']}

【兵部意见】
{state['bing_bu_opinion']}

【刑部意见】
{state['xing_bu_opinion']}

【工部意见】
{state['gong_bu_opinion']}"""
    prompt = f"{YU_SHI_TAI_PROMPT}\n\n【尚书省执行分案】\n{state['shang_shu_plan']}\n\n【六部会办意见汇总】\n{six_bu}"
    result = call_kimi(prompt)
    return {
        **state,
        "yu_shi_tai_ruling": result,
        "current_phase": "御史台-裁决完成",
        "messages": state["messages"] + [("御史台", result)]
    }

# ============ 条件路由 ============

def should_continue_to_yushitai(state: AgentState) -> str:
    required = ["li_bu_opinion", "hu_bu_opinion", "li_yi_bu_opinion",
                "bing_bu_opinion", "xing_bu_opinion", "gong_bu_opinion"]
    return "御史台" if all(state.get(f) for f in required) else END

# ============ 构建工作流 ============

def create_workflow():
    workflow = StateGraph(AgentState)

    workflow.add_node("中书省", zhong_shu_sheng_node)
    workflow.add_node("门下省", men_xia_sheng_node)
    workflow.add_node("尚书省", shang_shu_sheng_node)
    workflow.add_node("吏部", li_bu_node)
    workflow.add_node("户部", hu_bu_node)
    workflow.add_node("礼部", li_yi_bu_node)
    workflow.add_node("兵部", bing_bu_node)
    workflow.add_node("刑部", xing_bu_node)
    workflow.add_node("工部", gong_bu_node)
    workflow.add_node("御史台", yu_shi_tai_node)

    workflow.set_entry_point("中书省")

    # 三省流程
    workflow.add_edge("中书省", "门下省")
    workflow.add_edge("门下省", "尚书省")

    # 六部并行
    for bu in ["吏部", "户部", "礼部", "兵部", "刑部", "工部"]:
        workflow.add_edge("尚书省", bu)

    # 六部 → 御史台
    workflow.add_conditional_edges(
        "工部",
        should_continue_to_yushitai,
        {"御史台": "御史台", "": END}
    )

    workflow.add_edge("御史台", END)
    return workflow.compile()

# ============ 运行 ============

def run_system(task: str):
    print("=" * 60)
    print("🏛️ 三省六部智能体系统启动")
    print("=" * 60)
    print(f"\n【圣意】\n{task}\n")

    initial_state = AgentState(
        task=task,
        zhong_shu_draft="",
        men_xia_review="",
        shang_shu_plan="",
        li_bu_opinion="",
        hu_bu_opinion="",
        li_yi_bu_opinion="",
        bing_bu_opinion="",
        xing_bu_opinion="",
        gong_bu_opinion="",
        yu_shi_tai_ruling="",
        current_phase="等待中书省处理",
        messages=[]
    )

    result = create_workflow().invoke(initial_state)

    print("\n" + "=" * 60)
    print("📜 三省决议")
    print("=" * 60)
    print("\n【中书省草案】(Qwen思考模式)")
    print(result["zhong_shu_draft"])
    print("\n【门下省审议】(GPT)")
    print(result["men_xia_review"])
    print("\n【尚书省分案】(Qwen思考模式)")
    print(result["shang_shu_plan"])

    print("\n" + "=" * 60)
    print("⚔️ 六部会办")
    print("=" * 60)
    print("\n【吏部意见】(MiniMax)")
    print(result["li_bu_opinion"])
    print("\n【户部意见】(Qwen思考模式)")
    print(result["hu_bu_opinion"])
    print("\n【礼部意见】(Qwen思考模式)")
    print(result["li_yi_bu_opinion"])
    print("\n【兵部意见】(Qwen思考模式)")
    print(result["bing_bu_opinion"])
    print("\n【刑部意见】(Qwen思考模式)")
    print(result["xing_bu_opinion"])
    print("\n【工部意见】(Qwen思考模式)")
    print(result["gong_bu_opinion"])

    print("\n" + "=" * 60)
    print("⚖️ 御史台裁决 (Kimi)")
    print("=" * 60)
    print(result["yu_shi_tai_ruling"])

    print("\n" + "=" * 60)
    print("✅ 工作流程完成")
    print("=" * 60)

    return result


if __name__ == "__main__":
    example_task = "开发一个用户登录系统"
    run_system(example_task)
