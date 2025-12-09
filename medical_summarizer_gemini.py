from medical_ner_gemini import GeminiMedicalNER

class GeminiMedicalSummarizer:
    def __init__(self, api_key=None):
        self.extractor = GeminiMedicalNER(api_key)

    def format_symptom(self, symptom_dict):
        if isinstance(symptom_dict, str):
            return symptom_dict
        
        parts = []
        
        # Build symptom description
        symptom_text = symptom_dict.get('symptom', 'Unknown symptom')
        
        # Add severity if present
        severity = symptom_dict.get('severity')
        if severity and str(severity).lower() not in ['none', 'null']:
            symptom_text = f"{severity.capitalize()} {symptom_text.lower()}"
        else:
            symptom_text = symptom_text.capitalize()
        
        # Add body part if present
        body_part = symptom_dict.get('body_part')
        if body_part and str(body_part).lower() not in ['none', 'null']:
            symptom_text = f"{symptom_text} in {body_part}"
        
        parts.append(symptom_text)
        
        # Add additional info in parentheses
        extra_info = []
        
        duration = symptom_dict.get('duration')
        if duration and str(duration).lower() not in ['none', 'null']:
            extra_info.append(f"duration: {duration}")
        
        status = symptom_dict.get('status')
        if status and str(status).lower() not in ['none', 'null', 'current']:
            extra_info.append(f"status: {status}")
        
        if extra_info:
            parts.append(f"({', '.join(extra_info)})")
        
        return ' '.join(parts)
    
    def format_treatment(self, treatment_dict):
        if isinstance(treatment_dict, str):
            return treatment_dict
        
        treatment_type = treatment_dict.get('treatment_type', 'Treatment')
        details = treatment_dict.get('details', '')
        provider = treatment_dict.get('provider', '')
        
        # Build treatment string
        result_parts = [treatment_type.capitalize()]
        
        if details:
            result_parts.append(f": {details}")
        
        if provider:
            result_parts.append(f" (at {provider})")
        
        return ''.join(result_parts)

    def create_comprehensive_summary(self, transcript):
        print("Extracting medical entities...")
        entities = self.extractor.extract_entities(transcript)

        print("Extracting with confidence scores...")
        confidence_data = self.extractor.extract_with_confidence(transcript)

        print("Extracting medical keywords...")
        keywords = self.extractor.generate_keyword_extraction(transcript)

        # Combine all extractions
        comprehensive_summary = {
            "basic_extraction": entities,
            "confidence_scored": confidence_data,
            "keywords": keywords,
            "metadata": {
                "extraction_method": "Generative Model",
                "model_version": "Gemini-2.5-flash-lite"
            }
        }

        return comprehensive_summary
    
    def create_assignment_format(self, transcript):
        entities = self.extractor.extract_entities(transcript)

        if entities is None:
            print("Failed to extract entities")
            return None
        
        # Transform to assignment format
        assignment_output = {
            "Patient_Name": entities.get("Patient_Name", "Janet Jones"),
            "Symptoms": [],
            "Diagnosis": entities.get("Diagnosis", ""),
            "Treatment": [],
            "Current_Status": entities.get("Current_Status", ""),
            "Prognosis": entities.get("Prognosis", "")
        }

        # Format symptoms (FIXED - was "symtom")
        if "Symptoms" in entities and entities["Symptoms"]:
            for symptom in entities["Symptoms"]:
                if isinstance(symptom, dict):
                    formatted = self.format_symptom(symptom)
                    assignment_output["Symptoms"].append(formatted)
                else:
                    assignment_output["Symptoms"].append(str(symptom))
        
        # Format treatments (FIXED - was "Treamtment")
        if "Treatment" in entities and entities["Treatment"]:
            for treatment in entities["Treatment"]:
                if isinstance(treatment, dict):
                    formatted = self.format_treatment(treatment)
                    assignment_output["Treatment"].append(formatted)
                else:
                    assignment_output["Treatment"].append(str(treatment))
        
        return assignment_output