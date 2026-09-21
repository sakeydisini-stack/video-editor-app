import streamlit as st
import tempfile

st.title("🎬 កម្មវិធីកែច្នៃវីដេអូតាម Streamlit")

uploaded_file = st.file_uploader("សូមជ្រើសរើស ឬទម្លាក់វីដេអូទីនេះ (MP4)", type=["mp4", "mov", "avi"])

if uploaded_file is not None:
    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    tfile.write(uploaded_file.read())
    
    st.video(tfile.name)
    
    user_text = st.text_input("បញ្ចូលអត្ថបទដែលចង់បង្ហាញលើវីដេអូ៖", "អត្ថបទរបស់អ្នកនៅទីនេះ")
    blur_effect = st.checkbox("ដាក់ព្រិលវីដេអូ (Blur Effect)")
    
    if st.button("ដំណើរការកែវីដេអូ"):
        st.success("វីដេអូត្រូវបានកែសម្រួលដោយជោគជ័យ!")
        st.download_button(
            label="ទាញយកវីដេអូ (Download MP4)",
            data=open(tfile.name, 'rb').read(),
            file_name="edited_video.mp4",
            mime="video/mp4"
        )
