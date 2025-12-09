from sentiment_analyzer import MedicalSentimentAnalyzer
from intent_detector import GeminiIntentDetector  
import json
import os

class CompleteSentimentIntentAnalyzer:
    def __init__(self, api_key=None):
        print("=" * 60)
        print("INITIALIZING HYBRID ANALYZERS")
        print("=" * 60)
        print("Architecture:")
        print("  • Sentiment: Gemini 2.0 Flash Lite")
        print("  • Intent: Gemini 2.0 Flash Lite")
        print()
        
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')
        
        self.sentiment_analyzer = MedicalSentimentAnalyzer(api_key=api_key)
        self.intent_detector = GeminiIntentDetector(api_key=api_key)
        
        print("=" * 60)
        print("ALL MODELS LOADED SUCCESSFULLY")
        print("=" * 60)
        print()
    
    def parse_conversation(self, transcript):
        lines = transcript.strip().split('\n')
        conversation = []
        current_speaker = None
        current_text = []
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            if line.startswith('>'):
                line = line[1:].strip()
            
            if not line or line.startswith('['):
                continue
            
            if "**Physician:**" in line or "**Patient:**" in line:
                # Save previous turn
                if current_speaker and current_text:
                    text = " ".join(current_text).strip()
                    if text:  # Only add non-empty text
                        conversation.append({
                            "speaker": current_speaker,
                            "text": text
                        })
                
                if "**Physician:**" in line:
                    current_speaker = "Physician"
                    text = line.split("**Physician:**")[1].strip().strip('*').strip()
                else:
                    current_speaker = "Patient"
                    text = line.split("**Patient:**")[1].strip().strip('*').strip()
                
                current_text = [text] if text else []
            else:
                if current_speaker:
                    cleaned = line.strip('*').strip()
                    if cleaned:
                        current_text.append(cleaned)
        
        if current_speaker and current_text:
            text = " ".join(current_text).strip()
            if text:
                conversation.append({
                    "speaker": current_speaker,
                    "text": text
                })
        
        return conversation
    
    def analyze_complete(self, transcript):
        # Parse conversation
        conversation = self.parse_conversation(transcript)
        print(f"📝 Parsed {len(conversation)} conversation turns")
        patient_count = sum(1 for t in conversation if t['speaker'] == 'Patient')
        print(f"   Patient statements: {patient_count}")
        print()
        
        # Analyze sentiment
        print("🎭 Analyzing sentiment...")
        sentiment_results = self.sentiment_analyzer.analyze_conversation(conversation)
        overall_sentiment = self.sentiment_analyzer.get_overall_sentiment(sentiment_results)
        print(f"   Overall sentiment: {overall_sentiment['overall_sentiment']}")
        print()
        
        # Analyze intent
        print("🎯 Detecting intent...")
        intent_results = self.intent_detector.analyze_conversation(conversation)
        intent_summary = self.intent_detector.get_intent_summary(intent_results)
        print(f"   Dominant intent: {intent_summary['dominant_intent']}")
        print()
        
        # Combine results
        combined_results = []
        for i, turn in enumerate([t for t in conversation if t['speaker'] == 'Patient']):
            sentiment = sentiment_results[i] if i < len(sentiment_results) else {}
            intent = intent_results[i] if i < len(intent_results) else {}
            
            # Extract emotional indicators
            emotional_indicators = self.sentiment_analyzer.extract_emotional_indicators(turn['text'])
            
            combined_results.append({
                "statement": turn['text'][:150] + "..." if len(turn['text']) > 150 else turn['text'],
                "sentiment": sentiment.get('sentiment', 'Unknown'),
                "sentiment_confidence": sentiment.get('confidence', 0.0),
                "intent": intent.get('primary_intent', 'Unknown'),
                "intent_confidence": intent.get('confidence', 0.0),
                "emotional_indicators": [ei['keyword'] for ei in emotional_indicators],
                "intent_reasoning": intent.get('reasoning', '')
            })
        
        return {
            "individual_analyses": combined_results,
            "overall_sentiment": overall_sentiment,
            "intent_summary": intent_summary,
            "conversation_stats": {
                "total_turns": len(conversation),
                "patient_statements": patient_count,
                "physician_statements": len(conversation) - patient_count
            }
        }
    
    def create_assignment_format(self, transcript, sample_statement=None):
        if sample_statement:
            # Analyze single statement
            sentiment = self.sentiment_analyzer.analyze_sentiment(sample_statement)
            intent = self.intent_detector.detect_intent(sample_statement)
            
            return {
                "Statement": sample_statement,
                "Sentiment": sentiment['sentiment'],
                "Sentiment_Confidence": sentiment['confidence'],
                "Intent": intent['primary_intent'],
                "Intent_Confidence": intent['confidence']
            }
        else:
            # Analyze full conversation
            complete_analysis = self.analyze_complete(transcript)
            
            # Find a good example statement
            patient_statements = complete_analysis['individual_analyses']
            
            # Find statement with concern/worry
            example_statement = None
            for stmt in patient_statements:
                if stmt['sentiment'] in ['Anxious', 'Concerned'] or \
                   any(word in stmt['emotional_indicators'] for word in ['worried', 'concern']):
                    example_statement = stmt
                    break
            
            if not example_statement and patient_statements:
                example_statement = patient_statements[0]
            
            result = {
                "Overall_Analysis": {
                    "Dominant_Sentiment": complete_analysis['overall_sentiment']['overall_sentiment'],
                    "Sentiment_Confidence": complete_analysis['overall_sentiment']['confidence'],
                    "Dominant_Intent": complete_analysis['intent_summary']['dominant_intent'],
                    "Sentiment_Distribution": complete_analysis['overall_sentiment'].get('distribution', {}),
                    "Intent_Distribution": complete_analysis['intent_summary']['distribution']
                },
                "All_Patient_Analyses": patient_statements
            }
            
            if example_statement:
                result["Example_Analysis"] = {
                    "Statement": example_statement['statement'],
                    "Sentiment": example_statement['sentiment'],
                    "Sentiment_Confidence": example_statement['sentiment_confidence'],
                    "Intent": example_statement['intent'],
                    "Intent_Confidence": example_statement['intent_confidence']
                }
            
            return result