import pandas as pd
import streamlit as st
from utils.auth import require_auth, render_sidebar
from utils.db import get_quiz_attempts

st.set_page_config(page_title="Progress | IntelliLearn", page_icon="📈", layout="wide")
require_auth()
render_sidebar()

st.title("Learning Progress")

attempts = get_quiz_attempts()

if not attempts:
    st.info("No quiz attempts yet. Complete a quiz to generate analytics.")
    st.stop()

df = pd.DataFrame(attempts)
df["percentage"] = pd.to_numeric(df["percentage"])
df["created_at"] = pd.to_datetime(df["created_at"])

avg = df["percentage"].mean()
best = df["percentage"].max()
latest = df.iloc[-1]["percentage"]

c1, c2, c3 = st.columns(3)
c1.metric("Average score", f"{avg:.1f}%")
c2.metric("Best score", f"{best:.1f}%")
c3.metric("Latest score", f"{latest:.1f}%")

st.subheader("Score over time")
st.line_chart(df.set_index("created_at")[["percentage"]])

st.subheader("Performance by topic")
topic_df = df.groupby("topic", as_index=True)["percentage"].mean().sort_values()
st.bar_chart(topic_df)

weak = topic_df[topic_df < 70]
if not weak.empty:
    st.warning(
        "Topics to revise: "
        + ", ".join(f"{topic} ({score:.0f}%)" for topic, score in weak.items())
    )
else:
    st.success("No topic is currently below the 70% revision threshold.")
