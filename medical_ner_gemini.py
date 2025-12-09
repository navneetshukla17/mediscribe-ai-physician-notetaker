import os
import google.generativeai as genai
import json
from dotenv import load_dotenv

# Load api key
load_dotenv()

class GeminiMedicalNER:
    def __init__(self, api_key=None):
        if api_key == None:
            api_key = os.getenv("GEMINI_API_KEY")
        
        genai.configure(api_key=api_key)
        
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')

        # model configuration
        self.generation_config = {
            "temperature": 0.2,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048
        }


    def extract_entities(self, transcript):
        prompt = f"""You are a medical NLP expert. Extract structured medical information from the following physician-patient conversation transcript.

TRANSCRIPT:
{transcript}

Extract the following information and return ONLY a valid JSON object (no markdown, no code blocks, just pure JSON):

{{
  "Patient_Name": "Full name of the patient",
  "Symptoms": [
    {{
      "symptom": "name of symptom",
      "severity": "mild/moderate/severe",
      "duration": "how long",
      "body_part": "affected area",
      "status": "current/resolved/improving"
    }}
  ],
  "Diagnosis": "Primary diagnosis given by physician",
  "Treatment": [
    {{
      "treatment_type": "physiotherapy/medication/procedure",
      "details": "specific details like '10 sessions of physiotherapy'",
      "provider": "where treatment was given (if mentioned)"
    }}
  ],
  "Current_Status": "Patient's current condition description",
  "Prognosis": "Expected outcome or recovery timeline",
  "Accident_Details": {{
    "date": "when accident occurred",
    "location": "where it happened",
    "mechanism": "how injury occurred",
    "immediate_impact": "immediate injuries"
  }},
  "Physical_Examination": {{
    "findings": ["list of examination findings"],
    "mobility": "assessment of range of motion",
    "tenderness": "any tender areas noted"
  }},
  "Timeline": [
    {{
      "event": "description of event",
      "timepoint": "when it occurred",
      "significance": "why it matters"
    }}
  ]
}}

IMPORTANT RULES:
1. Extract ONLY information explicitly stated in the transcript
2. If information is missing, use null
3. Do NOT invent or infer information not in the text
4. Return ONLY valid JSON, nothing else
5. Use exact quotes from transcript where possible
6. For symptoms, identify severity from context (e.g., "really bad" = severe)

"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )
            
            # Parse JSON from response
            response_text = response.text.strip()

            # Remove markdown code if present
            if response_text.startswith("```json"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()
            elif response_text.startswith("```"):
                response_text.replace("```", "").strip()
            
            # Parse JSON
            extracted_data = json.loads(response_text)

            return extracted_data
        
        except json.JSONDecodeError as e:
            print(f"JSON parsing error!: {e}")
            print(f"Raw response: {response_text}")
            return None
        except Exception as e:
            print(f"Error: {e}")
            return None
        

    def extract_with_confidence(self, transcript):
        prompt = f"""You are a medical NLP expert. Extract medical information from this transcript and rate your confidence for each extraction.
        TRANSCRIPT:
{transcript}

Return a JSON object where each extracted piece of information includes a confidence score (0.0 to 1.0):

{{
  "Patient_Name": {{
    "value": "name",
    "confidence": 0.95,
    "source": "explicitly stated/inferred from context"
  }},
  "Symptoms": [
    {{
      "symptom": "symptom name",
      "confidence": 0.9,
      "evidence": "quote from transcript supporting this"
    }}
  ],
  ... (continue for all fields)
}}

Rate confidence based on:
- 1.0: Explicitly stated, no ambiguity
- 0.8-0.9: Clearly implied with strong context
- 0.6-0.7: Reasonable inference from context
- 0.4-0.5: Weak inference, multiple interpretations possible
- <0.4: Highly uncertain or missing

Return ONLY valid JSON.

"""
        try:
            response = self.model.generate_content(
                prompt,
                generation_config=self.generation_config
            )

            response_text = response.text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            return json.loads(response_text)
        
        except Exception as e:
            print(f"Error in confidence extraction: {e}")
            return None
        

    def generate_keyword_extraction(self, transcript):
        prompt = f"""Extract the most important medical keywords and phrases from this transcript.
        TRANSCRIPT:
{transcript}

Return a JSON array of important medical terms with their category:

{{
  "keywords": [
    {{
      "term": "whiplash injury",
      "category": "diagnosis",
      "importance": "high",
      "context": "brief context where it appears"
    }},
    {{
      "term": "physiotherapy",
      "category": "treatment",
      "importance": "high",
      "context": "10 sessions mentioned"
    }}
  ]
}}

Categories: symptom, diagnosis, treatment, body_part, temporal, severity_indicator, outcome

Return ONLY valid JSON.
"""
        try:
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()

            # Clean response
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            return json.loads(response_text)
        
        except Exception as e:
            print(f"Error in keyword extraction: {e}")
            return None

