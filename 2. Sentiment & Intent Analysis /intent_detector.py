import google.generativeai as genai
import os
import json
from dotenv import load_dotenv

load_dotenv()

class GeminiIntentDetector:    
    def __init__(self, api_key=None):
        print("Loading Gemini intent detector...")
        
        if api_key is None:
            api_key = os.getenv("GEMINI_API_KEY")
        
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found. Please set it as an environment variable or pass it to the constructor.")
        
        genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
        self.intent_categories = [
            "seeking reassurance",
            "reporting symptoms",
            "expressing concern",
            "asking questions",
            "providing information",
            "describing timeline",
            "expressing gratitude",
            "describing impact on life"
        ]
        
        print(f"Gemini intent detector loaded")
        print(f"Intent categories: {len(self.intent_categories)}\n")
    
    def detect_intent(self, text, categories=None):
        if not text or len(text.strip()) == 0:
            return {
                "text": text,
                "primary_intent": "unknown",
                "confidence": 0.0,
                "all_scores": {}
            }
        
        if categories is None:
            categories = self.intent_categories
        
        # Create prompt for Gemini
        prompt = f"""You are an expert in analyzing medical conversation intent.

Analyze the intent of this patient statement and classify it into ONE of these categories:
{', '.join(categories)}

Patient statement: "{text}"

Return ONLY a valid JSON object (no markdown, no code blocks, just pure JSON):
{{
  "primary_intent": "the most appropriate category from the list",
  "confidence": 0.85,
  "reasoning": "brief 1-sentence explanation",
  "all_scores": {{
    "seeking reassurance": 0.85,
    "reporting symptoms": 0.10,
    "expressing concern": 0.05,
    "asking questions": 0.00,
    "providing information": 0.00,
    "describing timeline": 0.00,
    "expressing gratitude": 0.00,
    "describing impact on life": 0.00
  }}
}}

IMPORTANT:
- Choose only from the provided categories
- Confidence should be 0.0 to 1.0
- Include scores for all categories in all_scores
- Return ONLY valid JSON
"""
        
        try:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "top_p": 0.95,
                    "max_output_tokens": 1024
                }
            )
            
            response_text = response.text.strip()
            
            # Clean response
            if "```json" in response_text:
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            result = json.loads(response_text)
            
            return {
                "text": text[:100] + "..." if len(text) > 100 else text,
                "primary_intent": result.get("primary_intent", "unknown"),
                "confidence": round(result.get("confidence", 0.0), 3),
                "all_scores": result.get("all_scores", {}),
                "reasoning": result.get("reasoning", "")
            }
        
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            print(f"Raw response: {response_text[:200]}")
            return {
                "text": text,
                "primary_intent": "error",
                "confidence": 0.0,
                "all_scores": {}
            }
        except Exception as e:
            print(f"Error detecting intent: {e}")
            return {
                "text": text,
                "primary_intent": "error",
                "confidence": 0.0,
                "all_scores": {}
            }
    
    def detect_multi_intent(self, text, categories=None, threshold=0.3):
        if categories is None:
            categories = self.intent_categories
        
        result = self.detect_intent(text, categories)
        
        if not result.get('all_scores'):
            return []
        
        # Filter by threshold
        intents = [
            {
                "intent": label,
                "confidence": round(score, 3)
            }
            for label, score in result['all_scores'].items()
            if score >= threshold
        ]
        
        # Sort by confidence
        intents.sort(key=lambda x: x['confidence'], reverse=True)
        
        return intents
    
    def analyze_conversation(self, conversation):
        results = []
        
        for turn in conversation:
            if turn['speaker'] == 'Patient':  # Focus on patient statements
                analysis = self.detect_intent(turn['text'])
                analysis['speaker'] = turn['speaker']
                results.append(analysis)
        
        return results
    
    def get_intent_summary(self, intents):
        if not intents:
            return {
                "dominant_intent": "unknown",
                "distribution": {}
            }
        
        # Count intents
        intent_counts = {}
        
        for i in intents:
            intent = i.get('primary_intent', 'unknown')
            if intent not in intent_counts:
                intent_counts[intent] = 0
            intent_counts[intent] += 1
        
        # Find dominant
        if intent_counts:
            dominant = max(intent_counts.items(), key=lambda x: x[1])
        else:
            dominant = ("unknown", 0)
        
        return {
            "dominant_intent": dominant[0],
            "distribution": intent_counts,
            "total_statements": len(intents)
        }