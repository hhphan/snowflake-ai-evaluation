import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

load_dotenv()

st.set_page_config(page_title="Snowflake AI Evaluation", layout="wide")

page = st.sidebar.radio("Navigation", ["Chat", "Evaluation Dashboard"])

# chat page
if page == "Chat":
    st.title("Customer Support Agent")
    st.caption("Ask questions about orders — e.g. 'What is the status of order 1?'")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask about an order..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Looking up order details..."):
                from src.agent.graph import app
                result = app.invoke({"messages": [HumanMessage(content=prompt)]})
                answer = result["messages"][-1].content
            st.write(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})

# eval dashboard
else:
    st.title("Evaluation Dashboard")
    st.caption("Golden suite pass/fail results by evaluation run.")

    try:
        from src.utils.snowflake_client import execute_query
        import pandas as pd

        rows = execute_query(
            "SELECT * FROM ANALYTICS_DB.MARTS.MART_EVAL_RESULTS_SUMMARY ORDER BY RUN_TIMESTAMP DESC"
        )

        if not rows:
            st.info("No evaluation runs yet. Run `python -m src.evaluation.pipeline` first.")
        else:
            df = pd.DataFrame(rows)
            df.columns = [c.lower() for c in df.columns]

            # Summary cards for the latest run
            latest = df.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Pass Rate", f"{latest['pass_rate']:.0%}")
            c2.metric("P90 Score", f"{latest['p90_score']:.2f}")
            c3.metric("Avg Score", f"{latest['avg_score']:.2f}")
            c4.metric("Questions", int(latest["total_questions"]))

            st.divider()
            st.subheader("All Runs")
            st.dataframe(
                df[["run_timestamp", "total_questions", "pass_rate", "avg_score", "p90_score", "pass_count", "fail_count"]],
                use_container_width=True,
            )

            st.subheader("Pass Rate Over Time")
            chart_df = df[["run_timestamp", "pass_rate"]].sort_values("run_timestamp")
            st.line_chart(chart_df.set_index("run_timestamp")["pass_rate"])

    except Exception as e:
        st.error(f"Could not load evaluation results: {e}")
        st.info("Run `python -m src.evaluation.pipeline` to generate results first.")
