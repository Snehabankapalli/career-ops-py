"""Streamlit dashboard for Career-Ops pipeline."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from career_ops.pipeline import Pipeline
from career_ops.tracker import ApplicationStatus

# Page config
st.set_page_config(
    page_title="Career-Ops Dashboard",
    page_icon="💼",
    layout="wide",
)

# Initialize pipeline
@st.cache_resource
def get_pipeline():
    return Pipeline()

pipeline = get_pipeline()

# Sidebar
st.sidebar.title("💼 Career-Ops")
st.sidebar.markdown("AI-powered job search automation")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "🔍 Evaluate Job", "📋 Applications", "📈 Analytics"],
)

# Dashboard page
if page == "📊 Dashboard":
    st.title("Job Search Dashboard")

    # Stats cards
    stats = pipeline.get_pipeline_stats()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Applications", stats.total)
    with col2:
        st.metric("Strong Apply", stats.strong_apply_count)
    with col3:
        st.metric("Avg Score", f"{stats.average_score}/5")
    with col4:
        st.metric("Response Rate", f"{stats.response_rate}%")

    # Status breakdown
    st.subheader("Pipeline Status")
    status_df = pd.DataFrame([
        {"Status": k, "Count": v}
        for k, v in stats.by_status.items()
    ])

    fig = px.bar(
        status_df,
        x="Status",
        y="Count",
        color="Status",
        color_discrete_sequence=px.colors.qualitative.Set3,
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

    # Quick actions
    st.subheader("Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 View Strong Apply Jobs", use_container_width=True):
            st.session_state.page = "📋 Applications"
            st.rerun()
    with col2:
        if st.button("🔍 Evaluate New Job", use_container_width=True):
            st.session_state.page = "🔍 Evaluate Job"
            st.rerun()

# Evaluate Job page
elif page == "🔍 Evaluate Job":
    st.title("Evaluate Job Opportunity")

    job_url = st.text_input("Job URL", placeholder="https://boards.greenhouse.io/...")

    col1, col2 = st.columns([1, 3])
    with col1:
        generate_pdf = st.checkbox("Generate PDF", value=True)

    if st.button("🚀 Evaluate", type="primary", use_container_width=True):
        if job_url:
            with st.spinner("Scraping and analyzing..."):
                import asyncio
                result = asyncio.run(pipeline.evaluate_job(job_url, generate_pdf))

            # Display results
            evaluation = result["evaluation"]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Score", f"{evaluation.overall_score}/5")
            with col2:
                st.metric("Grade", evaluation.grade)
            with col3:
                st.metric("Recommendation", evaluation.recommendation.replace("_", " ").title())

            # Expanders for details
            with st.expander("📝 Reasoning", expanded=True):
                st.write(evaluation.reasoning)

            with st.expander("✅ Strengths"):
                for strength in evaluation.strengths:
                    st.write(f"• {strength}")

            with st.expander("⚠️ Gaps"):
                for gap in evaluation.gaps:
                    st.write(f"• {gap}")

            with st.expander("🎯 Interview Prep"):
                interview = evaluation.interview_prep
                if "star_stories" in interview:
                    st.write("**STAR Stories to Prepare:**")
                    for story in interview["star_stories"]:
                        st.write(f"• {story}")
                if "questions_to_ask" in interview:
                    st.write("**Questions to Ask:**")
                    for q in interview["questions_to_ask"]:
                        st.write(f"• {q}")

            if result["pdf_path"]:
                st.success(f"✅ PDF generated: {result['pdf_path']}")

        else:
            st.warning("Please enter a job URL")

# Applications page
elif page == "📋 Applications":
    st.title("Application Pipeline")

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox(
            "Status",
            ["All"] + [s.value for s in ApplicationStatus],
        )
    with col2:
        min_score = st.slider("Min Score", 0.0, 5.0, 0.0, 0.5)
    with col3:
        search = st.text_input("Search", placeholder="Company or role...")

    # Get applications
    status = None if status_filter == "All" else ApplicationStatus(status_filter)
    applications = pipeline.get_applications(status=status, min_score=min_score if min_score > 0 else None)

    # Search filter
    if search:
        applications = [a for a in applications if search.lower() in a.company.lower() or search.lower() in a.role.lower()]

    # Display as dataframe
    if applications:
        df_data = []
        for app in applications:
            df_data.append({
                "ID": app.id,
                "Company": app.company,
                "Role": app.role,
                "Score": app.score,
                "Grade": app.grade,
                "Status": app.status,
                "Date": app.created_at.strftime("%Y-%m-%d"),
                "Location": app.location or "N/A",
            })

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Status update
        st.subheader("Update Status")
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            app_id = st.number_input("Application ID", min_value=1, step=1)
        with col2:
            new_status = st.selectbox("New Status", [s.value for s in ApplicationStatus])
        with col3:
            if st.button("Update", use_container_width=True):
                pipeline.update_application_status(app_id, ApplicationStatus(new_status))
                st.success("Status updated!")
                st.rerun()
    else:
        st.info("No applications found matching your filters.")

# Analytics page
elif page == "📈 Analytics":
    st.title("Pipeline Analytics")

    stats = pipeline.get_pipeline_stats()

    # Score distribution
    applications = pipeline.get_applications()
    if applications:
        scores = [a.score for a in applications if a.score is not None]
        if scores:
            fig = go.Figure(data=[go.Histogram(x=scores, nbinsx=10)])
            fig.update_layout(
                title="Score Distribution",
                xaxis_title="Score",
                yaxis_title="Count",
            )
            st.plotly_chart(fig, use_container_width=True)

        # Timeline (placeholder - would need actual dates)
        st.subheader("Activity Timeline")
        st.info("Timeline visualization coming soon!")
    else:
        st.info("No data yet. Start evaluating jobs to see analytics!")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Built with ❤️ by Sneha Bankapalli")
