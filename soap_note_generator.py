import json
import re
from typing import Dict, Any, Optional
import google.generativeai as genai


class SOAPNoteGenerator:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')
        
    def create_soap_prompt(self, transcript: str) -> str:
        prompt = f"""You are a medical documentation expert. Convert the following medical conversation transcript into a structured SOAP note format.

SOAP Format Guidelines:
- **Subjective**: Patient's reported symptoms, complaints, and medical history
- **Objective**: Observable findings from physical examination, vital signs, test results
- **Assessment**: Physician's diagnosis and clinical reasoning
- **Plan**: Treatment recommendations, medications, follow-up instructions

Transcript:
{transcript}

Generate a SOAP note in the following JSON format:
{{
  "Subjective": {{
    "Chief_Complaint": "Main reason for visit",
    "History_of_Present_Illness": "Detailed description of current condition",
    "Past_Medical_History": "Relevant past medical events",
    "Patient_Concerns": "Any worries or questions expressed by patient"
  }},
  "Objective": {{
    "Physical_Exam": "Findings from physical examination",
    "Observations": "Visual observations of patient condition",
    "Vital_Signs": "If mentioned in transcript"
  }},
  "Assessment": {{
    "Diagnosis": "Primary diagnosis",
    "Severity": "Condition severity assessment",
    "Prognosis": "Expected outcome"
  }},
  "Plan": {{
    "Treatment": "Recommended treatments and interventions",
    "Medications": "If any medications prescribed or mentioned",
    "Follow-Up": "Follow-up instructions and timeline",
    "Patient_Education": "Any advice or education provided"
  }}
}}

Return ONLY valid JSON without any markdown formatting or explanations."""
        
        return prompt
    
    def generate_soap_note(self, transcript: str) -> Dict[str, Any]:
        try:
            prompt = self.create_soap_prompt(transcript)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,  
                    max_output_tokens=2048,
                )
            )
            
            # Extract JSON from response
            soap_note = self._parse_response(response.text)
            
            return soap_note
            
        except Exception as e:
            print(f"Error generating SOAP note: {str(e)}")
            return self._get_empty_soap_structure()
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        clean_text = re.sub(r'```json\n?', '', response_text)
        clean_text = re.sub(r'```\n?', '', clean_text)
        clean_text = clean_text.strip()
        
        try:
            soap_note = json.loads(clean_text)
            return soap_note
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', clean_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except:
                    pass
            
            print("Failed to parse JSON response")
            return self._get_empty_soap_structure()
    
    def _get_empty_soap_structure(self) -> Dict[str, Any]:
        return {
            "Subjective": {
                "Chief_Complaint": "",
                "History_of_Present_Illness": "",
                "Past_Medical_History": "",
                "Patient_Concerns": ""
            },
            "Objective": {
                "Physical_Exam": "",
                "Observations": "",
                "Vital_Signs": ""
            },
            "Assessment": {
                "Diagnosis": "",
                "Severity": "",
                "Prognosis": ""
            },
            "Plan": {
                "Treatment": "",
                "Medications": "",
                "Follow-Up": "",
                "Patient_Education": ""
            }
        }
    
    def format_soap_note(self, soap_note: Dict[str, Any]) -> str:
        output = []
        output.append("=" * 60)
        output.append("SOAP NOTE")
        output.append("=" * 60)
        
        for section, content in soap_note.items():
            output.append(f"\n{section.upper()}:")
            output.append("-" * 60)
            
            if isinstance(content, dict):
                for key, value in content.items():
                    if value:
                        formatted_key = key.replace("_", " ").title()
                        output.append(f"{formatted_key}: {value}")
            else:
                output.append(str(content))
        
        output.append("\n" + "=" * 60)
        return "\n".join(output)


# Example usage and testing
def main():    
    # Sample transcript from the exercise
    sample_transcript = """
    Physician: Good morning, Ms. Jones. How are you feeling today?
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
    Physician: You're very welcome, Ms. Jones. Take care, and don't hesitate to reach out if you need anything.
    """
    
    API_KEY = "AIzaSyCExJ73OZLDaiIhRSw9mDdOadsupzHM--c"
    
    print("SOAP Note Generator - Module 3")
    print("=" * 60)
    
    # Initialize generator
    generator = SOAPNoteGenerator(api_key=API_KEY)
    
    # Generate SOAP note
    print("\nGenerating SOAP note from transcript...")
    soap_note = generator.generate_soap_note(sample_transcript)
    
    # Display formatted output
    print("\n" + generator.format_soap_note(soap_note))
    
    # Save as JSON
    with open('soap_note_output.json', 'w') as f:
        json.dump(soap_note, f, indent=2)
    print("\nSOAP note saved to 'soap_note_output.json'")


if __name__ == "__main__":
    main()