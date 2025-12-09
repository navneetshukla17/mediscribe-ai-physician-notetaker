import google.generativeai as genai
import os
import json
import warnings
warnings.filterwarnings(action='ignore')


class MedicalSentimentAnalyzer:
    def __init__(self, api_key=None):
        print(f"Loading sentiment model: gemini-2.5-flash-lite")
        
        if api_key is None:
            api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found. Please set it as an environment variable or pass it to the constructor.")
        
        genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel('gemini-2.0-flash-lite')
        
        print(f"Gemini sentiment model loaded successfully\n")
    
    
    def analyze_sentiment(self, text):
        if not text or len(text.strip()) == 0:
            return {
                "text": text,
                "sentiment": "Neutral",
                "confidence": 0.0,
                "raw_label": None
            }
        
        # Create prompt for Gemini
        prompt = f"""Analyze the sentiment of the following medical patient statement and classify it into one of these categories:
- Reassured: Patient feels confident, positive, or relieved (high positivity)
- Neutral: Patient is calm, matter-of-fact, or shows mild emotions
- Concerned: Patient shows moderate worry or uncertainty
- Anxious: Patient expresses significant worry, fear, or distress

Patient statement: "{text}"

Respond ONLY with a JSON object in this exact format (no markdown, no code blocks):
{{
    "sentiment": "one of: Reassured, Neutral, Concerned, Anxious",
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation"
}}"""
        
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            return {
                "text": text,
                "sentiment": result.get("sentiment", "Neutral"),
                "confidence": round(float(result.get("confidence", 0.5)), 3),
                "raw_label": result.get("sentiment"),
                "raw_score": round(float(result.get("confidence", 0.5)), 3),
                "reasoning": result.get("reasoning", "")
            }
            
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return {
                "text": text,
                "sentiment": "Neutral",
                "confidence": 0.5,
                "raw_label": "NEUTRAL",
                "raw_score": 0.5,
                "reasoning": f"Error: {str(e)}"
            }
    
    
    def analyze_conversation(self, conversation):
        results = []
        
        for turn in conversation:
            if turn['speaker'] == 'Patient':
                analysis = self.analyze_sentiment(turn['text'])
                analysis['speaker'] = turn['speaker']
                results.append(analysis)
        
        return results
    
    
    def get_overall_sentiment(self, sentiments):
        if not sentiments:
            return {
                "overall_sentiment": "Neutral",
                "confidence": 0.0,
                "distribution": {}
            }
        
        # Count sentiments
        sentiment_counts = {}
        total_confidence = 0
        
        for s in sentiments:
            sentiment = s['sentiment']
            confidence = s['confidence']
            
            if sentiment not in sentiment_counts:
                sentiment_counts[sentiment] = {"count": 0, "total_confidence": 0}
            
            sentiment_counts[sentiment]['count'] += 1
            sentiment_counts[sentiment]['total_confidence'] += confidence
            total_confidence += confidence
        
        # Find dominant sentiment
        dominant_sentiment = max(
            sentiment_counts.items(),
            key=lambda x: (x[1]['count'], x[1]['total_confidence'])
        )
        
        avg_confidence = total_confidence / len(sentiments)
        
        return {
            "overall_sentiment": dominant_sentiment[0],
            "confidence": round(avg_confidence, 3),
            "distribution": {
                k: v['count'] for k, v in sentiment_counts.items()
            }
        }
    
    
    def extract_emotional_indicators(self, text):
        emotional_keywords = {
            'anxious': ['worried', 'anxious', 'nervous', 'scared', 'afraid', 'concerned', 'stressed'],
            'positive': ['better', 'good', 'great', 'relief', 'happy', 'glad', 'thankful', 'appreciate'],
            'negative': ['bad', 'worse', 'terrible', 'awful', 'pain', 'hurt', 'difficult', 'struggle'],
            'neutral': ['okay', 'fine', 'normal', 'alright', 'usual']
        }
        
        text_lower = text.lower()
        found_indicators = []
        
        for category, keywords in emotional_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    found_indicators.append({
                        'keyword': keyword,
                        'category': category
                    })
        
        return found_indicators