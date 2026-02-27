# import streamlit as st
# from capacity_planner import capacity_agent, CapacityState

# st.set_page_config(
#     page_title="AI Capacity Planner",
#     layout="centered"
# )

# st.title("AI Capacity Planning System")
# st.write("AI-driven machine and operator optimization")

# # Input form
# with st.form("capacity_form"):
#     target_qty = st.number_input(
#         "Target Quantity",
#         min_value=1,
#         value=500
#     )

#     deadline_hrs = st.number_input(
#         "Deadline (Hours)",
#         min_value=1,
#         value=72
#     )

#     part_id = st.text_input(
#         "Part ID",
#         value="P1001"
#     )

#     submit = st.form_submit_button("Generate Plan")

# # Run agent if form submitted
# if submit:
#     with st.spinner("Optimizing production plan..."):
#         try:
#             # Prepare input state
#             input_state: CapacityState = {
#                 "target_qty": target_qty,
#                 "deadline_hrs": deadline_hrs,
#                 "part_id": part_id,
#                 "feasible_machines": [],
#                 "machine_operator_pairs": [],
#                 "final_recommendation": {},
#                 "explanation": "",
#                 "historical_memory": []
#             }

#             # Call your agent directly
#             result = capacity_agent.invoke(input_state)
#             rec = result.get("final_recommendation", {})

#             # Check if a feasible plan was found
#             if rec.get("status") == "NO_FEASIBLE_PLAN":
#                 st.warning(" No feasible machine-operator plan found for these inputs.")
#             elif rec:  # Feasible plan exists
#                 st.success(" Optimal Plan Generated")

#                 st.subheader("Recommendation")
#                 st.write(f"**Machine ID:** {rec.get('machine_id', '-')}")
#                 st.write(f"**Operator:** {rec.get('operator_name', '-')}"
#                          f" ({rec.get('operator_id', '-')})")
#                 st.write(f"**Estimated Time:** {rec.get('final_time', '-')}")
#                 st.write(f"**Efficiency Score:** {rec.get('operator_efficiency', '-')}")
#                 st.write(f"**Failure Risk:** {rec.get('risk', '-')}")

#                 st.subheader("AI Explanation")
#                 explanation = result.get("explanation","No explanation available.")
#                 st.info(explanation)
#             else:
#                 st.warning(" No recommendation could be generated.")

#         except Exception as e:
#             st.error(f"Unexpected error occurred: {e}")




import streamlit as st
from capacity_planner import capacity_agent, CapacityState

# ----------------------------------
# Page Configuration
# ----------------------------------
st.set_page_config(
    page_title="AI Capacity Planner",
    layout="centered"
)

st.title("AI Capacity Planning System")
st.write("AI-driven machine and operator optimization")

# ----------------------------------
# Input Form
# ----------------------------------
with st.form("capacity_form"):
    target_qty = st.number_input(
        "Target Quantity",
        min_value=1,
        value=500
    )

    deadline_hrs = st.number_input(
        "Deadline (Hours)",
        min_value=1,
        value=72
    )

    part_id = st.text_input(
        "Part ID",
        value="P1001"
    )

    submit = st.form_submit_button("Generate Plan")

# ----------------------------------
# Run Agent
# ----------------------------------
if submit:
    with st.spinner("Optimizing production plan..."):
        try:
            # Prepare input state
            input_state: CapacityState = {
                "target_qty": target_qty,
                "deadline_hrs": deadline_hrs,
                "part_id": part_id,
                "feasible_machines": [],
                "machine_operator_pairs": [],
                "final_recommendation": None,
                "explanation": "",
                "historical_memory": []
            }

            # Invoke agent
            result = capacity_agent.invoke(input_state)

            recommendation = result.get("final_recommendation")
            explanation = result.get("explanation", "")

            # ----------------------------------
            # Display Result
            # ----------------------------------
            if not recommendation:
                st.warning("❌ No feasible machine-operator plan found for the given inputs.")
            else:
                st.success("✅ Optimal Plan Generated")

                st.subheader("📌 Recommendation")
                st.write(f"**Machine ID:** {recommendation.get('machine_id', '-')}")
                st.write(
                    f"**Operator:** {recommendation.get('operator_name', '-')}"
                    f" ({recommendation.get('operator_id', '-')})"
                )
                st.write(f"**Estimated Time (hrs):** {recommendation.get('final_time', '-')}")
                st.write(f"**Efficiency Score:** {recommendation.get('operator_efficiency', '-')}")
                st.write(f"**Failure Risk:** {recommendation.get('risk', '-')}")

                st.subheader("🧠 AI Explanation")
                st.info(explanation if explanation else "No explanation available.")

        except Exception as e:
            st.error(f"🚨 Unexpected error occurred: {str(e)}")