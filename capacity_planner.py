
import os
import json
import random
import pandas as pd
from typing import TypedDict, List, Dict, Optional

from dotenv import load_dotenv
from langgraph.graph import StateGraph
from langchain_groq import ChatGroq

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

PLAN = pd.read_csv(os.path.join(BASE_DIR, "plan_data.csv"))
AVAIL = pd.read_csv(os.path.join(BASE_DIR, "machine_availability.csv"))
OPS = pd.read_csv(os.path.join(BASE_DIR, "operator_efficiency.csv"))
PARTS = pd.read_csv(os.path.join(BASE_DIR, "part_cycle_time.csv"))


class CapacityState(TypedDict):
    target_qty: int
    deadline_hrs: int
    part_id: str

    feasible_machines: List[Dict]
    machine_operator_pairs: List[Dict]
    final_recommendation: Optional[Dict]
    explanation: str
    historical_memory: List[Dict]


def part_analysis_agent(state: CapacityState):
    part_df = PARTS[PARTS["part_id"] == state["part_id"]]
    state["feasible_machines"] = part_df.to_dict("records")
    return state


def machine_feasibility_agent(state: CapacityState):
    feasible = []

    for m in state["feasible_machines"]:
        plan_row = PLAN[PLAN["machine_id"] == m["machine_id"]]
        avail_row = AVAIL[AVAIL["machine_id"] == m["machine_id"]]

        if plan_row.empty or avail_row.empty:
            continue

        plan = plan_row.iloc[0]
        avail = avail_row.iloc[0]

        if not avail["is_available"]:
            continue

        if plan["uptime_percentage"] <= 0:
            continue

        if avail["criticality_level"] == "High" and avail["risk_of_failure"] > 0.15:
            continue

        prod_time = (m["cycle_time_seconds"] * state["target_qty"]) / 3600
        prod_time += m["setup_time_minutes"] / 60

        effective_time = prod_time / plan["uptime_percentage"]

        if effective_time <= state["deadline_hrs"]:
            feasible.append({
                "machine_id": m["machine_id"],
                "machine_type": plan["machine_type"],
                "effective_time": round(effective_time, 2),
                "risk": avail["risk_of_failure"]
            })

    state["feasible_machines"] = feasible
    return state


def operator_matching_agent(state: CapacityState):
    pairs = []

    for machine in state["feasible_machines"]:
        eligible_ops = OPS[
            OPS["preferred_machine_type"] == machine["machine_type"]
        ]

        for _, op in eligible_ops.iterrows():
            adjusted_time = machine["effective_time"] / op["efficiency_score"]

            if adjusted_time <= state["deadline_hrs"]:
                pairs.append({
                    "machine_id": machine["machine_id"],
                    "machine_type": machine["machine_type"],
                    "operator_id": op["operator_id"],
                    "operator_name": op["operator_name"],
                    "final_time": round(adjusted_time, 2),
                    "operator_efficiency": op["efficiency_score"],
                    "risk": machine["risk"]
                })

    state["machine_operator_pairs"] = pairs
    return state


def memory_retrieval_agent(state: CapacityState):
    try:
        with open("memory.json", "r") as f:
            memory = json.load(f)
    except FileNotFoundError:
        memory = []

    state["historical_memory"] = memory
    return state


def learning_agent(state: CapacityState):
    history = state["historical_memory"]
    pairs = state["machine_operator_pairs"]

    for pair in pairs:
        penalty = 0
        reward = 0

        for past in history:
            if (
                past["machine_id"] == pair["machine_id"]
                and past["operator_id"] == pair["operator_id"]
            ):
                if not past["success"]:
                    penalty += 0.1
                else:
                    reward += 0.05

        pair["learning_penalty"] = penalty
        pair["learning_reward"] = reward

    state["machine_operator_pairs"] = pairs
    return state



llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    groq_api_key=os.getenv("GROQ_API_KEY")
)


import re

def llm_selection_agent(state: CapacityState):
    pairs = state["machine_operator_pairs"]

    # If no pairs exist, then truly no feasible
    if not pairs:
        state["final_recommendation"] = None
        state["explanation"] = "No feasible machine-operator combination found."
        return state

    prompt = f"""
You are an AI Capacity Planning Optimization Engine.

Production Requirements:
- Quantity: {state['target_qty']}
- Deadline: {state['deadline_hrs']} hours
- Part ID: {state['part_id']}

Available Machine-Operator Options:
{json.dumps(pairs, indent=2)}

Select ONLY the single BEST combination.

Return ONLY ONE JSON object.
Do NOT return a list.
Do NOT rank.
Do NOT add markdown.
Do NOT add explanation outside JSON.

JSON format:
{{
  "machine_id": "...",
  "operator_id": "...",
  "operator_name": "...",
  "final_time": number,
  "operator_efficiency": number,
  "risk": number,
  "reasoning": "clear explanation"
}}
"""

    response = llm.invoke(prompt)
    raw_output = response.content.strip()


    raw_output = raw_output.replace("```json", "")
    raw_output = raw_output.replace("```", "").strip()

  
    match = re.search(r'\{.*\}', raw_output, re.DOTALL)

    if not match:
        state["final_recommendation"] = None
        state["explanation"] = "LLM did not return valid JSON."
        return state

    json_str = match.group(0)

    try:
        decision = json.loads(json_str)
        state["final_recommendation"] = decision
        state["explanation"] = decision.get("reasoning", "")
    except Exception as e:
        state["final_recommendation"] = None
        state["explanation"] = f"JSON parsing failed: {str(e)}"

    return state


def memory_update_agent(state: CapacityState):
    rec = state["final_recommendation"]

    if rec is None:
        return state

    success = random.choices([True, False], weights=[0.8, 0.2])[0]

    record = {
        "part_id": state["part_id"],
        "machine_id": rec["machine_id"],
        "operator_id": rec["operator_id"],
        "operator_name": rec["operator_name"],
        "success": success,
        "time_taken": rec["final_time"],
        "risk": rec["risk"]
    }

    try:
        with open("memory.json", "r") as f:
            memory = json.load(f)
    except FileNotFoundError:
        memory = []

    memory.append(record)

    with open("memory.json", "w") as f:
        json.dump(memory, f, indent=4)

    state["historical_memory"] = memory
    return state


graph = StateGraph(CapacityState)

graph.add_node("part_agent", part_analysis_agent)
graph.add_node("machine_agent", machine_feasibility_agent)
graph.add_node("operator_agent", operator_matching_agent)
graph.add_node("memory_reader", memory_retrieval_agent)
graph.add_node("learning_agent", learning_agent)
graph.add_node("llm_selector", llm_selection_agent)
graph.add_node("memory_writer", memory_update_agent)

graph.set_entry_point("part_agent")

graph.add_edge("part_agent", "machine_agent")
graph.add_edge("machine_agent", "operator_agent")
graph.add_edge("operator_agent", "memory_reader")
graph.add_edge("memory_reader", "learning_agent")
graph.add_edge("learning_agent", "llm_selector")
graph.add_edge("llm_selector", "memory_writer")

capacity_agent = graph.compile()

# RUN

if __name__ == "__main__":

    input_state: CapacityState = {
        "target_qty": 500,
        "deadline_hrs": 72,
        "part_id": "P1001",
        "feasible_machines": [],
        "machine_operator_pairs": [],
        "final_recommendation": None,   
        "explanation": "",
        "historical_memory": []
    }

    result = capacity_agent.invoke(input_state)

    print("\n AI AGENT RECOMMENDATION\n")

    best = result.get("final_recommendation")

    if isinstance(best, dict) and best.get("machine_id"):
        print(f"Machine        : {best['machine_id']}")
        print(f"Operator       : {best['operator_name']} ({best['operator_id']})")
        print(f"Estimated Time : {best['final_time']} hrs")
        print(f"Efficiency     : {best['operator_efficiency']}")
        print(f"Risk           : {best['risk']}")
    else:
        print("No feasible recommendation found.")

    print("\n AI EXPLANATION \n")

    print(result["explanation"])
