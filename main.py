# from fastapi import FastAPI
# from capacity_planner import capacity_agent, CapacityState

# app = FastAPI()

# @app.post("/plan_capacity/")
# def plan_capacity(target_qty: int, deadline_hrs: int, part_id: str):
#     input_state: CapacityState = {
#         "target_qty": target_qty,
#         "deadline_hrs": deadline_hrs,
#         "part_id": part_id,
#         "feasible_machines": [],
#         "machine_operator_pairs": [],
#         "final_recommendation": {},
#         "explanation": "",
#         "historical_memory": []
#     }
#     result = capacity_agent.invoke(input_state)
#     return {
#         "recommendation": result["final_recommendation"],
#         "explanation": result["explanation"]
#     }


# app.py

# from fastapi import FastAPI, HTTPException
# from capacity_planner import capacity_agent, CapacityState
# import uvicorn


# app = FastAPI(title="AI Capacity Planner")

# @app.post("/plan_capacity/")
# def plan_capacity(target_qty: int, deadline_hrs: int, part_id: str):

#     input_state: CapacityState = {
#         "target_qty": target_qty,
#         "deadline_hrs": deadline_hrs,
#         "part_id": part_id,
#         "feasible_machines": [],
#         "machine_operator_pairs": [],
#         "final_recommendation": {},
#         "explanation": "",
#         "historical_memory": []
#     }

#     result = capacity_agent.invoke(input_state)

#     if not result["final_recommendation"]:
#         raise HTTPException(status_code=404, detail="No feasible plan found")

#     return {
#         "recommendation": result["final_recommendation"],
#         "explanation": result["explanation"]
#     }


# if __name__ == "__main__":
#     uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from capacity_planner import capacity_agent, CapacityState
import uvicorn

app = FastAPI(
    title="AI Capacity Planner",
    description="Agentic AI based Machine-Operator Capacity Optimization API",
    version="1.0.0"
)

# -----------------------------
# Request Model
# -----------------------------
class CapacityRequest(BaseModel):
    target_qty: int = Field(..., example=500)
    deadline_hrs: int = Field(..., example=10)
    part_id: str = Field(..., example="P001")


# -----------------------------
# Response Model
# -----------------------------
class CapacityResponse(BaseModel):
    recommendation: Dict[str, Any]
    explanation: Optional[str]


# -----------------------------
# API Endpoint
# -----------------------------
@app.post("/plan_capacity/", response_model=CapacityResponse)
def plan_capacity(request: CapacityRequest):

    try:
        input_state: CapacityState = {
            "target_qty": request.target_qty,
            "deadline_hrs": request.deadline_hrs,
            "part_id": request.part_id,
            "feasible_machines": [],
            "machine_operator_pairs": [],
            "final_recommendation": None,
            "explanation": "",
            "historical_memory": []
        }

        result = capacity_agent.invoke(input_state)

        # If no recommendation found
        if not result.get("final_recommendation"):
            raise HTTPException(
                status_code=404,
                detail="No feasible machine-operator plan found"
            )

        return CapacityResponse(
            recommendation=result["final_recommendation"],
            explanation=result.get("explanation", "")
        )

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )


# -----------------------------
# Run Server
# -----------------------------
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)