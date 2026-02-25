import streamlit as st
import requests
import json
import tempfile
import os

API_URL = "https://brand-guardian-api.grayriver-3197115b.centralindia.azurecontainerapps.io/audit"

st.set_page_config(
    page_title="Brand Guardian AI",
    layout="wide"
)

st.title("Brand Guardian AI",text_alignment="center")
st.markdown("Upload a video to audit brand compliance.")

uploaded_file = st.file_uploader(
    "Upload Video File",
    type=["mp4", "mov", "avi", "mkv"]
)

if uploaded_file:

    col1, col2 = st.columns([1, 1])

    # ----------------------
    # LEFT SIDE: VIDEO
    # ----------------------
    with col1:
        st.subheader("Uploaded Video")

        # Save temporarily for display
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(uploaded_file.read())
            temp_video_path = tmp_file.name

        st.video(temp_video_path)

    # ----------------------
    # RIGHT SIDE: PROCESSING
    # ----------------------
    with col2:
        st.subheader("Compliance Report")

        if st.button("Run Audit"):

            with st.spinner("Running compliance workflow..."):

                try:
                    files = {
                        "file": (
                            uploaded_file.name,
                            open(temp_video_path, "rb"),
                            uploaded_file.type
                        )
                    }

                    response = requests.post(
                        API_URL,
                        files=files,
                        timeout=600  # 10 minutes
                    )

                    if response.status_code == 200:
                        data = response.json()

                        st.success(f"Status: {data['status']}")
                        st.markdown("---")

                        st.markdown("###Final Report")
                        st.write(data["final_report"])

                        st.markdown("---")
                        st.markdown("### ⚠ Compliance Issues")

                        if data["compliance_results"]:
                            for issue in data["compliance_results"]:
                                with st.container():
                                    st.markdown(
                                        f"""
                                        **Category:** {issue['category']}  
                                        **Severity:** {issue['severity']}  
                                        **Description:** {issue['description']}
                                        """
                                    )
                                    st.markdown("---")
                        else:
                            st.success("No compliance issues detected.")

                        # Optional raw JSON
                        with st.expander("View Raw JSON"):
                            st.json(data)

                    else:
                        st.error(f"API Error: {response.text}")

                except Exception as e:
                    st.error(f"Request Failed: {str(e)}")

    # Cleanup temp file
    if os.path.exists(temp_video_path):
        os.remove(temp_video_path)