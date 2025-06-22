import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from fpdf import FPDF
import time

# Download NLTK data
nltk.download('punkt')
nltk.download('stopwords')

# Setup page
st.set_page_config(
    page_title="YouTube Summarizer",
    page_icon="🎥",
    layout="centered"
)
st.title("YouTube Video Summarizer")
st.write("Paste a YouTube URL to generate a summary")

# Function to extract video ID
def extract_video_id(url):
    pattern = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|youtu\.be\/)([^\"&?\/\s]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

# Function to get transcript
def get_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([entry['text'] for entry in transcript])
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

# Function to clean text
def clean_text(text):
    text = re.sub(r'\[.*?\]', '', text)  # Remove [Music]
    text = re.sub(r'\(.*?\)', '', text)  # Remove (Applause)
    text = re.sub(r'\s+', ' ', text)     # Remove extra spaces
    return text.strip()

# Function to summarize text
def summarize_text(text, num_sentences=5):
    # Tokenize the text
    words = word_tokenize(text)
    sentences = sent_tokenize(text)
    
    # Remove stopwords
    stop_words = set(stopwords.words("english"))
    words = [word.lower() for word in words if word.isalnum() and word.lower() not in stop_words]
    
    # Calculate word frequency
    freq_dist = nltk.FreqDist(words)
    
    # Score sentences
    sentence_scores = {}
    for i, sentence in enumerate(sentences):
        for word in word_tokenize(sentence.lower()):
            if word in freq_dist:
                if i not in sentence_scores:
                    sentence_scores[i] = freq_dist[word]
                else:
                    sentence_scores[i] += freq_dist[word]
    
    # Get top sentences
    if not sentence_scores:
        return text[:500] + "..."  # Fallback if no scores
    
    top_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True)[:num_sentences]
    summary = " ".join([sentences[i] for i in sorted(top_sentences)])
    return summary

# Function to create PDF
def create_pdf(summary):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, summary)
    return pdf.output(dest='S').encode('latin1')

# Main app
url = st.text_input("Enter YouTube URL:", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Generate Summary"):
    if not url:
        st.warning("Please enter a YouTube URL")
    else:
        video_id = extract_video_id(url)
        if not video_id:
            st.error("Invalid YouTube URL")
        else:
            # Get video info
            try:
                yt = YouTube(f"https://youtube.com/watch?v={video_id}")
                st.subheader(yt.title)
                st.image(yt.thumbnail_url, width=300)
            except:
                st.info("Couldn't load video details")
            
            # Get transcript
            with st.spinner("Fetching transcript..."):
                transcript = get_transcript(video_id)
            
            if transcript:
                # Clean text
                with st.spinner("Processing text..."):
                    clean_transcript = clean_text(transcript)
                
                # Generate summary
                with st.spinner("Creating summary..."):
                    summary = summarize_text(clean_transcript)
                
                # Display results
                st.success("Summary Generated!")
                st.subheader("Summary:")
                st.write(summary)
                
                # Download options
                st.subheader("Download Options:")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.download_button(
                        "Download as TXT",
                        summary,
                        f"{video_id}_summary.txt",
                        "text/plain"
                    )
                
                with col2:
                    pdf_data = create_pdf(summary)
                    st.download_button(
                        "Download as PDF",
                        pdf_data,
                        f"{video_id}_summary.pdf",
                        "application/pdf"
                    )
            else:
                st.error("Failed to get transcript. Try another video.")