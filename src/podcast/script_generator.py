import logging
import json
from typing import List, Dict, Any
from dataclasses import dataclass

from crewai import LLM

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PodcastScript:
    """Represents a podcast script with metadata"""
    script: List[Dict[str, str]]
    source_document: str
    total_lines: int
    estimated_duration: str

    def get_speaker_lines(self, speaker: str) -> List[str]:
        return [item[speaker] for item in self.script if speaker in item]

    def to_json(self) -> str:
        return json.dumps({
            'script': self.script,
            'metadata': {
                'source_document': self.source_document,
                'total_lines': self.total_lines,
                'estimated_duration': self.estimated_duration
            }
        }, indent=2)


class PodcastScriptGenerator:
    def __init__(self, groq_api_key: str, model_name: str = "llama-3.3-70b-versatile"):
        self.llm = LLM(
            model=f"groq/{model_name}",
            api_key=groq_api_key,
            temperature=0.7,
            max_tokens=4000
        )
        logger.info(f"Podcast script generator initialized with Groq {model_name}")


    def generate_script_from_text(
        self,
        text_content: str,
        source_name: str = "Text Input",
        podcast_style: str = "conversational",
        target_duration: str = "10 minutes"
    ) -> PodcastScript:

        logger.info("Generating podcast script from text input")

        script_data = self._generate_conversation_script(
            text_content,
            podcast_style,
            target_duration
        )

        podcast_script = PodcastScript(
            script=script_data['script'],
            source_document=source_name,
            total_lines=len(script_data['script']),
            estimated_duration=target_duration
        )

        logger.info(f"Generated script with {podcast_script.total_lines} lines")
        return podcast_script

    def _generate_conversation_script(
        self,
        document_content: str,
        podcast_style: str,
        target_duration: str
    ) -> Dict[str, Any]:

        style_prompts = {
            "conversational": "Create a natural, engaging narration by a single speaker discussing the document in a friendly, conversational tone.",
            "educational": "Create an educational narration where the speaker explains concepts clearly and thoroughly for listeners.",
            "interview": "Create a narrative format where the speaker presents information as if sharing insights from an interview or discussion.",
            "debate": "Create a thoughtful narration where the speaker explores different perspectives and viewpoints on the topics."
        }

        style_instruction = style_prompts.get(podcast_style, style_prompts["conversational"])

        duration_guidelines = {
            "5 minutes": "Keep the narration concise, focusing on 3-4 main points with brief explanations.",
            "10 minutes": "Cover the key topics thoroughly with good explanations and examples.",
            "15 minutes": "Provide comprehensive coverage with detailed discussions and multiple examples.",
            "20 minutes": "Create an in-depth exploration with extensive analysis and supporting details."
        }

        duration_guide = duration_guidelines.get(target_duration, duration_guidelines["10 minutes"])

        prompt = f"""Using the following document, create a podcast script for a single speaker narration.

STYLE GUIDELINES:
{style_instruction}

DURATION GUIDELINES:
{duration_guide}

NARRATION RULES:
1. Break the content into natural segments (2-4 sentences each)
2. The narration should flow naturally with smooth transitions
3. Use engaging, conversational language that's easy to understand
4. Include a brief introduction at the start and wrap-up at the end
5. Break down complex concepts into digestible explanations
6. Maintain professional grammar and punctuation throughout
7. Make it engaging for listeners who haven't read the document

RESPONSE FORMAT:
Respond with a valid JSON object containing a 'script' array. Each array element should be an object with 'Speaker' as the key and the narration segment as the value.

Example format:
{{
  "script": [
    {{"Speaker": "Welcome to this podcast! Today we're diving into some fascinating insights from this document..."}},
    {{"Speaker": "Let's start by exploring the first key concept. This is particularly interesting because..."}}
  ]
}}

DOCUMENT CONTENT:
{document_content[:8000]}

Generate an engaging {target_duration} podcast script now:"""

        try:
            response = self.llm.call(prompt)
            script_data = json.loads(response)

            if 'script' not in script_data or not isinstance(script_data['script'], list):
                raise ValueError("Invalid script format returned by LLM")

            validated_script = self._validate_and_clean_script(script_data['script'])

            return {'script': validated_script}

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            response_clean = response.strip()
            if response_clean.startswith('```json'):
                response_clean = response_clean[7:-3]
            elif response_clean.startswith('```'):
                response_clean = response_clean[3:-3]

            try:
                script_data = json.loads(response_clean)
                validated_script = self._validate_and_clean_script(script_data['script'])
                return {'script': validated_script}
            except:
                raise ValueError(f"Could not parse LLM response as valid JSON: {response}")

        except Exception as e:
            logger.error(f"Error generating script: {str(e)}")
            raise

    def _validate_and_clean_script(self, script: List[Dict[str, str]]) -> List[Dict[str, str]]:
        cleaned_script = []
        for item in script:
            if not isinstance(item, dict) or len(item) != 1:
                continue

            speaker, dialogue = next(iter(item.items()))
            speaker = speaker.strip()

            # Normalize to single "Speaker"
            if speaker.lower() not in ["speaker"]:
                speaker = "Speaker"

            dialogue = dialogue.strip()
            if not dialogue:
                continue
            if not dialogue.endswith(('.', '!', '?')):
                dialogue += '.'

            cleaned_script.append({speaker: dialogue})

        if len(cleaned_script) < 2:
            raise ValueError("Generated script is too short or invalid")

        return cleaned_script
