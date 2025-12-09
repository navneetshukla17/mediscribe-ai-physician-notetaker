import streamlit as st
import json
import os
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from dotenv import load_dotenv


try:
    from medical_ner_gemini import GeminiMedicalNER
    from medical_summarizer_gemini import GeminiMedicalSummarizer
    from sentiment_intent_analyzer import CompleteSentimentIntentAnalyzer
    from soap_note_generator import SOAPNoteGenerator
    MODULES_LOADED = True
except ImportError as e:
    MODULES_LOADED = False
    IMPORT_ERROR = str(e)
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="MediScribe AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .section-header {
        color: #1f77b4;
        font-size: 1.8rem;
        font-weight: bold;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Sample transcript
SAMPLE_TRANSCRIPT = """Physician: Good morning, Ms. Jones. How are you feeling today?

Patient: Good morning, doctor. I'm doing better, but I still have some discomfort now and then.

Physician: I understand you were in a car accident last September. Can you walk me through what happened?

Patient: Yes, it was on September 1st, around 12:30 in the afternoon. I was driving from Cheadle Hulme to Manchester when I had to stop in traffic. Out of nowhere, another car hit me from behind, which pushed my car into the one in front.

Physician: That sounds like a strong impact. Were you wearing your seatbelt?

Patient: Yes, I always do.

Physician: What did you feel immediately after the accident?

Patient: At first, I was just shocked. But then I realized I had hit my head on the steering wheel, and I could feel pain in my neck and back almost right away.

Physician: Did you seek medical attention at that time?

Patient: Yes, I went to Moss Bank Accident and Emergency. They checked me over and said it was a whiplash injury, but they didn't do any X-rays. They just gave me some advice and sent me home.

Physician: How did things progress after that?

Patient: The first four weeks were rough. My neck and back pain were really bad—I had trouble sleeping and had to take painkillers regularly. It started improving after that, but I had to go through ten sessions of physiotherapy to help with the stiffness and discomfort.

Physician: That makes sense. Are you still experiencing pain now?

Patient: It's not constant, but I do get occasional backaches. It's nothing like before, though.

Physician: That's good to hear. Have you noticed any other effects, like anxiety while driving or difficulty concentrating?

Patient: No, nothing like that. I don't feel nervous driving, and I haven't had any emotional issues from the accident.

Physician: And how has this impacted your daily life? Work, hobbies, anything like that?

Patient: I had to take a week off work, but after that, I was back to my usual routine. It hasn't really stopped me from doing anything.

Physician: That's encouraging. Let's go ahead and do a physical examination to check your mobility and any lingering pain.

[Physical Examination Conducted]

Physician: Everything looks good. Your neck and back have a full range of movement, and there's no tenderness or signs of lasting damage. Your muscles and spine seem to be in good condition.

Patient: That's a relief!

Physician: Yes, your recovery so far has been quite positive. Given your progress, I'd expect you to make a full recovery within six months of the accident. There are no signs of long-term damage or degeneration.

Patient: That's great to hear. So, I don't need to worry about this affecting me in the future?

Physician: That's right. I don't foresee any long-term impact on your work or daily life. If anything changes or you experience worsening symptoms, you can always come back for a follow-up. But at this point, you're on track for a full recovery.

Patient: Thank you, doctor. I appreciate it.

Physician: You're very welcome, Ms. Jones. Take care, and don't hesitate to reach out if you need anything."""


def initialize_session_state():
    """Initialize session state variables"""
    if 'api_key' not in st.session_state:
        st.session_state.api_key = os.getenv('GEMINI_API_KEY', '')
    if 'transcript' not in st.session_state:
        st.session_state.transcript = SAMPLE_TRANSCRIPT
    if 'ner_results' not in st.session_state:
        st.session_state.ner_results = None
    if 'sentiment_results' not in st.session_state:
        st.session_state.sentiment_results = None
    if 'soap_results' not in st.session_state:
        st.session_state.soap_results = None


def render_header():
    """Render main header"""
    st.markdown('<div class="main-header">🩺 MediScribe AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Intelligent Medical Documentation System</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Module 1", "Medical NER", "✅")
    with col2:
        st.metric("Module 2", "Sentiment & Intent", "✅")
    with col3:
        st.metric("Module 3", "SOAP Notes", "✅")
    
    st.markdown("---")


def sidebar_config():
    """Sidebar configuration"""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        api_key = st.text_input(
            "Gemini API Key",
            value=st.session_state.api_key,
            type="password",
            help="Enter your Google Gemini API key"
        )
        st.session_state.api_key = api_key
        
        st.markdown("---")
        
        st.header("📝 About")
        st.markdown("""
        **MediScribe AI** transforms physician-patient conversations into structured clinical documentation.
        
        **Features:**
        - Medical entity extraction
        - Sentiment analysis
        - Intent detection
        - SOAP note generation
        
        **Tech Stack:**
        - Google Gemini 2.5 Flash
        - Python + Streamlit
        - Plotly visualizations
        """)
        
        st.markdown("---")
        st.markdown("**Developed by:** Navneet")
        st.markdown("**For:** Emitrr AI Engineer Intern Assignment")


def module1_ner():
    """Module 1: Medical NER & Summarization"""
    st.markdown('<div class="section-header">📋 Module 1: Medical NER & Summarization</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Input Transcript")
        transcript = st.text_area(
            "Enter or edit the physician-patient conversation:",
            value=st.session_state.transcript,
            height=300,
            key="ner_transcript"
        )
        st.session_state.transcript = transcript
    
    with col2:
        st.subheader("Quick Actions")
        if st.button("🔄 Load Sample Transcript", use_container_width=True):
            st.session_state.transcript = SAMPLE_TRANSCRIPT
            st.rerun()
        
        if st.button("🗑️ Clear Transcript", use_container_width=True):
            st.session_state.transcript = ""
            st.rerun()
    
    if st.button("🚀 Extract Medical Entities", type="primary", use_container_width=True):
        if not st.session_state.api_key:
            st.error("⚠️ Please enter your Gemini API key in the sidebar")
            return
        
        if not transcript.strip():
            st.warning("⚠️ Please enter a transcript")
            return
        
        with st.spinner("🔍 Analyzing transcript with Gemini AI..."):
            try:
                summarizer = GeminiMedicalSummarizer(api_key=st.session_state.api_key)
                results = summarizer.create_assignment_format(transcript)
                st.session_state.ner_results = results
                st.success("✅ Analysis complete!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                return
    
    # Display results
    if st.session_state.ner_results:
        st.markdown("---")
        st.subheader("📊 Extraction Results")
        
        results = st.session_state.ner_results
        
        # Summary cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{len(results.get('Symptoms', []))}</h3>
                <p>Symptoms</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{len(results.get('Treatment', []))}</h3>
                <p>Treatments</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            diagnosis = results.get('Diagnosis', 'N/A')
            st.markdown(f"""
            <div class="metric-card">
                <h3>1</h3>
                <p>Diagnosis</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>✓</h3>
                <p>Prognosis</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Detailed results
        tab1, tab2, tab3 = st.tabs(["📝 Summary", "🔍 Detailed View", "💾 JSON Output"])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**👤 Patient Information**")
                st.info(f"**Name:** {results.get('Patient_Name', 'N/A')}")
                
                st.markdown("**🩺 Diagnosis**")
                st.info(results.get('Diagnosis', 'N/A'))
                
                st.markdown("**📊 Current Status**")
                st.success(results.get('Current_Status', 'N/A'))
            
            with col2:
                st.markdown("**🎯 Prognosis**")
                st.success(results.get('Prognosis', 'N/A'))
                
                st.markdown("**💊 Treatment**")
                for treatment in results.get('Treatment', []):
                    st.write(f"• {treatment}")
        
        with tab2:
            st.markdown("**🤒 Symptoms**")
            for i, symptom in enumerate(results.get('Symptoms', []), 1):
                st.write(f"{i}. {symptom}")
            
            st.markdown("**💉 Treatment Details**")
            for i, treatment in enumerate(results.get('Treatment', []), 1):
                st.write(f"{i}. {treatment}")
        
        with tab3:
            st.json(results)
            
            # Download button
            json_str = json.dumps(results, indent=2)
            st.download_button(
                label="📥 Download JSON",
                data=json_str,
                file_name=f"medical_ner_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )


def module2_sentiment():
    """Module 2: Sentiment & Intent Analysis"""
    st.markdown('<div class="section-header">🎭 Module 2: Sentiment & Intent Analysis</div>', unsafe_allow_html=True)
    
    # Input options
    analysis_type = st.radio(
        "Choose analysis type:",
        ["Single Statement", "Full Conversation"],
        horizontal=True
    )
    
    if analysis_type == "Single Statement":
        statement = st.text_area(
            "Enter patient statement:",
            value="I'm a bit worried about my back pain, but I hope it gets better soon.",
            height=100
        )
        
        if st.button("🔍 Analyze Statement", type="primary"):
            if not st.session_state.api_key:
                st.error("⚠️ Please enter your Gemini API key")
                return
            
            with st.spinner("Analyzing sentiment and intent..."):
                try:
                    analyzer = CompleteSentimentIntentAnalyzer(api_key=st.session_state.api_key)
                    results = analyzer.create_assignment_format(
                        st.session_state.transcript,
                        sample_statement=statement
                    )
                    st.session_state.sentiment_results = results
                    st.success("✅ Analysis complete!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    return
        
        # Display single statement results
        if st.session_state.sentiment_results and 'Statement' in st.session_state.sentiment_results:
            st.markdown("---")
            results = st.session_state.sentiment_results
            
            col1, col2 = st.columns(2)
            with col1:
                sentiment = results.get('Sentiment', 'Unknown')
                confidence = results.get('Sentiment_Confidence', 0)
                
                # Sentiment color coding
                color = {
                    'Anxious': '#ff6b6b',
                    'Concerned': '#ffa500',
                    'Neutral': '#4ecdc4',
                    'Reassured': '#95e1d3'
                }.get(sentiment, '#666')
                
                st.markdown(f"""
                <div style="background-color: {color}; padding: 2rem; border-radius: 10px; text-align: center; color: white;">
                    <h2>😊 Sentiment</h2>
                    <h1>{sentiment}</h1>
                    <p>Confidence: {confidence:.2%}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                intent = results.get('Intent', 'Unknown')
                intent_conf = results.get('Intent_Confidence', 0)
                
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; text-align: center; color: white;">
                    <h2>🎯 Intent</h2>
                    <h1>{intent}</h1>
                    <p>Confidence: {intent_conf:.2%}</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.json(results)
    
    else:  # Full Conversation
        transcript = st.text_area(
            "Enter conversation transcript:",
            value=st.session_state.transcript,
            height=200
        )
        
        if st.button("🔍 Analyze Conversation", type="primary"):
            if not st.session_state.api_key:
                st.error("⚠️ Please enter your Gemini API key")
                return
            
            with st.spinner("Analyzing full conversation..."):
                try:
                    analyzer = CompleteSentimentIntentAnalyzer(api_key=st.session_state.api_key)
                    results = analyzer.create_assignment_format(transcript)
                    st.session_state.sentiment_results = results
                    st.success("✅ Analysis complete!")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    return
        
        # Display full conversation results
        if st.session_state.sentiment_results and 'Overall_Analysis' in st.session_state.sentiment_results:
            st.markdown("---")
            results = st.session_state.sentiment_results
            overall = results['Overall_Analysis']
            
            # Overall metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Dominant Sentiment", overall['Dominant_Sentiment'])
            with col2:
                st.metric("Dominant Intent", overall['Dominant_Intent'])
            with col3:
                st.metric("Statements Analyzed", len(results['All_Patient_Analyses']))
            
            # Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Sentiment distribution pie chart
                sentiment_dist = overall.get('Sentiment_Distribution', {})
                if sentiment_dist:
                    fig = px.pie(
                        values=list(sentiment_dist.values()),
                        names=list(sentiment_dist.keys()),
                        title="Sentiment Distribution",
                        color_discrete_sequence=px.colors.qualitative.Set3
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Intent distribution
                intent_dist = overall.get('Intent_Distribution', {})
                if intent_dist:
                    fig = px.bar(
                        x=list(intent_dist.keys()),
                        y=list(intent_dist.values()),
                        title="Intent Distribution",
                        labels={'x': 'Intent', 'y': 'Count'},
                        color=list(intent_dist.values()),
                        color_continuous_scale='Viridis'
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            # Detailed analysis
            st.subheader("📊 Detailed Statement Analysis")
            for i, analysis in enumerate(results['All_Patient_Analyses'], 1):
                with st.expander(f"Statement {i}: {analysis['statement'][:50]}..."):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Sentiment:** {analysis['sentiment']}")
                        st.progress(analysis['sentiment_confidence'])
                    with col2:
                        st.write(f"**Intent:** {analysis['intent']}")
                        st.progress(analysis['intent_confidence'])
                    
                    if analysis.get('emotional_indicators'):
                        st.write("**Emotional Indicators:**", ", ".join(analysis['emotional_indicators']))


def module3_soap():
    """Module 3: SOAP Note Generation"""
    st.markdown('<div class="section-header">📝 Module 3: SOAP Note Generation</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <strong>SOAP Format:</strong> Subjective, Objective, Assessment, Plan - A structured medical documentation standard.
    </div>
    """, unsafe_allow_html=True)
    
    transcript = st.text_area(
        "Enter conversation transcript:",
        value=st.session_state.transcript,
        height=250
    )
    
    if st.button("📋 Generate SOAP Note", type="primary", use_container_width=True):
        if not st.session_state.api_key:
            st.error("⚠️ Please enter your Gemini API key")
            return
        
        with st.spinner("🔄 Generating SOAP note..."):
            try:
                generator = SOAPNoteGenerator(api_key=st.session_state.api_key)
                soap_note = generator.generate_soap_note(transcript)
                st.session_state.soap_results = soap_note
                st.success("✅ SOAP note generated successfully!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                return
    
    # Display SOAP note
    if st.session_state.soap_results:
        st.markdown("---")
        soap = st.session_state.soap_results
        
        # SOAP sections
        sections = ["Subjective", "Objective", "Assessment", "Plan"]
        colors = ["#e3f2fd", "#f3e5f5", "#fff3e0", "#e8f5e9"]
        icons = ["🗣️", "🔬", "🩺", "📋"]
        
        for section, color, icon in zip(sections, colors, icons):
            st.markdown(f"### {icon} {section}")
            
            section_data = soap.get(section, {})
            
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    if value and str(value).strip():
                        formatted_key = key.replace("_", " ").title()
                        st.markdown(f"""
                        <div style="background-color: {color}; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
                            <strong>{formatted_key}:</strong><br>
                            {value}
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background-color: {color}; padding: 1rem; border-radius: 8px; margin-bottom: 0.5rem;">
                    {section_data}
                </div>
                """, unsafe_allow_html=True)
        
        # Download options
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            json_str = json.dumps(soap, indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_str,
                file_name=f"soap_note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            # Format as text
            text_output = []
            for section in sections:
                text_output.append(f"\n{'='*60}\n{section.upper()}\n{'='*60}")
                section_data = soap.get(section, {})
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        if value:
                            text_output.append(f"\n{key.replace('_', ' ').title()}:\n{value}")
            
            text_str = "\n".join(text_output)
            st.download_button(
                label="📄 Download as Text",
                data=text_str,
                file_name=f"soap_note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                use_container_width=True
            )


def main():
    """Main application"""
    initialize_session_state()
    render_header()
    sidebar_config()
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Medical NER",
        "🎭 Sentiment & Intent",
        "📝 SOAP Notes",
        "ℹ️ About"
    ])
    
    with tab1:
        module1_ner()
    
    with tab2:
        module2_sentiment()
    
    with tab3:
        module3_soap()
    
    with tab4:
        st.markdown("""
        # 🩺 MediScribe AI
        
        ## Overview
        **MediScribe AI** is an intelligent medical documentation system that leverages Google's Gemini 2.5 Flash model
        to transform physician-patient conversations into structured clinical notes.
        
        ## Features
        
        ### Module 1: Medical NER & Summarization
        - Extract patient information, symptoms, diagnoses, treatments
        - Generate structured JSON output
        - Confidence scoring for extractions
        
        ### Module 2: Sentiment & Intent Analysis
        - Analyze patient emotional states
        - Detect conversation intents
        - Visualize sentiment and intent distributions
        
        ### Module 3: SOAP Note Generation
        - Automated SOAP format documentation
        - Clinical-ready structured notes
        - Export in multiple formats
        
        ## Technology Stack
        - **AI Model:** Google Gemini 2.5 Flash Lite
        - **Framework:** Python 3.8+, Streamlit
        - **Visualization:** Plotly, Matplotlib
        - **APIs:** Google Generative AI
        
        ## Assignment Details
        - **Company:** Emitrr
        - **Role:** AI Engineer Intern
        - **Developer:** Navneet
        - **Deadline:** December 10, 2025
        
        ## Contact
        For questions or feedback, please contact the developer.
        
        ---
        
        <div style="text-align: center; color: #666; padding: 2rem;">
            Built with ❤️ using Streamlit and Google Gemini AI
        </div>
        """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()