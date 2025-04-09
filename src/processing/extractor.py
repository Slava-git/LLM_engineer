from typing import Dict, List, Any, Tuple, Optional
import json
from haystack import component
from haystack.utils import Secret
from haystack.components.generators.openai import OpenAIGenerator
from ..config import logger, OPENAI_API_KEY

@component
class StructureExtractor:
    """
    A flexible structure extractor that uses LLM to decide what data to extract from notes
    and produces adaptable structured outputs with tags.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the StructureExtractor.
        
        Args:
            model: OpenAI model to use
        """

        if not OPENAI_API_KEY:
            logger.warning("No OpenAI API key provided. Structure extraction will not work.")
        
        self.generator = OpenAIGenerator(
            api_key=Secret.from_token(OPENAI_API_KEY), 
            model=model
        )
        
    @component.output_types(structured_data=Dict[str, Any], structure_type=str, suggested_tags=List[str], confidence=float)
    def run(self, text: str):
        """
        Extract structured data from text using a flexible approach where the LLM
        determines what fields to extract and suggests tags.
        
        Args:
            text: The note text to extract structured information from
            
        Returns:
            Dict containing the structured data, structure type, suggested tags, and confidence score
        """
        default_result = {
            "structured_data": {},
            "structure_type": "unknown",
            "suggested_tags": [],
            "confidence": 0.0
        }
        
        if not OPENAI_API_KEY:
            logger.warning("OpenAI API key not set. Skipping structure extraction.")
            return default_result
            
        prompt = self._create_extraction_prompt(text)
        
        try:
            response = self.generator.run(prompt=prompt)
            generated_text = response["replies"][0]
            
            structured_data, structure_type, suggested_tags, confidence = self._parse_response(generated_text)
            
            return {
                "structured_data": structured_data,
                "structure_type": structure_type,
                "suggested_tags": suggested_tags,
                "confidence": confidence
            }
            
        except Exception as e:
            logger.error(f"Error extracting structured data: {str(e)}")
            return default_result
    
    def _create_extraction_prompt(self, text: str) -> str:
        """
        Create a prompt to guide the LLM in extracting structured data and suggesting tags.
        
        Args:
            text: The note text
            
        Returns:
            Formatted prompt for the LLM
        """
        return f"""You are a specialized AI trained to extract structured data from notes.
        
Your task:
1. Analyze the note below and identify what kind of information it contains
2. Determine what fields would be most appropriate to extract 
3. Extract those fields and their values
4. Generate 3-7 relevant tags that would be useful for categorizing this note
5. Return your result in a specific JSON format that includes:
   - A "type" field indicating the general category of information (e.g., appointment, task, recipe, vocabulary, contact, etc.)
   - A "data" object containing all extracted fields
   - A "tags" array with relevant normalized tags (lowercase, no spaces, use underscores if needed)
   - A "confidence" score from 0.0 to 1.0 indicating how confident you are in the extraction

For example, if the note is about a dentist appointment, you might return:
```json
{{
  "type": "appointment",
  "data": {{
    "title": "Dentist Appointment",
    "date": "Monday",
    "time": "10:00",
    "location": null,
    "with": "Dr. Smith",
    "notes": null
  }},
  "tags": ["appointment", "dentist", "medical", "monday", "morning"],
  "confidence": 0.95
}}
```

But if it's a recipe, you might return completely different fields:
```json
{{
  "type": "recipe",
  "data": {{
    "dish": "Pasta Dinner",
    "ingredients": ["8 cups pasta", "12 cups water", "1 tbsp olive oil", "1 tbsp salt", "2 onions", "2 garlic cloves", "1 tbsp Italian seasoning"],
    "preparation": "Cook pasta according to package directions...",
    "cookTime": "15 minutes",
    "servings": 4
  }},
  "tags": ["recipe", "pasta", "dinner", "italian", "main_dish"],
  "confidence": 0.85
}}
```

The fields you extract should be specific to what makes sense for the type of note.
If you can't determine a clear structure, return "type": "note" with the best fields you can extract.

Note to analyze:
{text}

Return only valid JSON without explanation or other text.
"""

    def _parse_response(self, response: str) -> Tuple[Dict[str, Any], str, List[str], float]:
        """
        Parse the LLM response into structured data, tags and confidence.
        
        Args:
            response: The text response from the LLM
            
        Returns:
            Tuple of (structured_data, structure_type, suggested_tags, confidence)
        """
        try:

            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)

                structure_type = data.get("type", "unknown")
                structured_data = data.get("data", {})
                suggested_tags = data.get("tags", [])
                confidence = data.get("confidence", 0.0)
                
                return structured_data, structure_type, suggested_tags, confidence
            else:
                logger.warning("No JSON found in response")
                return {}, "unknown", [], 0.0
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            return {}, "unknown", [], 0.0
        except Exception as e:
            logger.error(f"Error processing response: {e}")
            return {}, "unknown", [], 0.0