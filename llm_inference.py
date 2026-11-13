"""
LLM inference pipeline for context experiment.

Supports: OpenAI (GPT-4, GPT-3.5), Anthropic (Claude), and HuggingFace models.
Includes Pydantic validation for structured output parsing.
"""

import os
import json
import time
import logging
from typing import Dict, List, Tuple, Optional, Literal
from abc import ABC, abstractmethod
import re
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, field_validator, ConfigDict, ValidationError

logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC RESPONSE MODELS
# ============================================================================

class IdeologyEnum(str, Enum):
    """Political ideology categories."""
    LEFT = "Left"
    CENTER = "Center"
    RIGHT = "Right"


class StanceEnum(str, Enum):
    """Stance categories toward political figures."""
    FAVOR = "favor"
    AGAINST = "against"
    NEUTRAL = "neutral"
    UNDECIDED = "undecided"


class StanceResponse(BaseModel):
    """Structured stance response for political figures."""
    Trump: Optional[StanceEnum] = None
    Biden: Optional[StanceEnum] = None

    model_config = ConfigDict(use_enum_values=False)

    @field_validator('Trump', 'Biden', mode='before')
    @classmethod
    def parse_stance(cls, v):
        """Parse stance from string if needed."""
        if v is None:
            return None
        if isinstance(v, str):
            v_lower = v.lower().strip()
            for stance in StanceEnum:
                if stance.value == v_lower:
                    return stance
            # Try partial matching
            for stance in StanceEnum:
                if stance.value in v_lower:
                    return stance
        return v


class IdeologyPrediction(BaseModel):
    """Ideology prediction with confidence."""
    label: IdeologyEnum
    confidence: int = Field(..., ge=0, le=100, description="Confidence 0-100%")
    reasoning: Optional[str] = None

    model_config = ConfigDict(use_enum_values=False)

    @field_validator('label', mode='before')
    @classmethod
    def parse_ideology(cls, v):
        """Parse ideology from string if needed."""
        if isinstance(v, str):
            v_lower = v.lower().strip()
            for ideo in IdeologyEnum:
                if ideo.value.lower() == v_lower:
                    return ideo
        return v

    @field_validator('confidence', mode='before')
    @classmethod
    def parse_confidence(cls, v):
        """Parse confidence from various formats."""
        if isinstance(v, str):
            # Remove % and convert to int
            v = v.rstrip('%').strip()
            v = int(float(v))
        # Clamp to 0-100
        return min(100, max(0, int(v)))


class StancePrediction(BaseModel):
    """Stance prediction with confidence."""
    stances: StanceResponse
    confidence: int = Field(..., ge=0, le=100, description="Confidence 0-100%")
    reasoning: Optional[str] = None

    model_config = ConfigDict(use_enum_values=False)

    @field_validator('confidence', mode='before')
    @classmethod
    def parse_confidence(cls, v):
        """Parse confidence from various formats."""
        if isinstance(v, str):
            v = v.rstrip('%').strip()
            v = int(float(v))
        return min(100, max(0, int(v)))


class AnalysisOutput(BaseModel):
    """Complete analysis output with both ideology and stance predictions."""
    ideology: IdeologyPrediction
    stance: StancePrediction
    data_quality: Optional[Dict] = None
    raw_response: Optional[str] = None

    model_config = ConfigDict(use_enum_values=False)


# ============================================================================
# PROMPT TEMPLATES
# ============================================================================

SYSTEM_PROMPT = """You are a political discourse analyst specializing in social media content.
Your task is to infer users' political ideology and their stance toward specific political figures.

CRITICAL INSTRUCTIONS:
1. Use ONLY the information provided in the context blocks.
2. Do NOT use external knowledge or assumptions beyond what's given.
3. If a context field is empty, acknowledge it and do not speculate.
4. Be precise and evidence-based in your assessment.
5. When confidence is low, report it honestly rather than guessing.

You must output structured JSON responses in the exact format specified."""


ANALYSIS_PROMPT_TEMPLATE = """You are a political discourse analyst specializing in social media content.

TASK: Analyze the provided context and determine:
1. The author's political ideology (Left, Center, or Right)
2. The author's stance toward Donald Trump and Joe Biden (if mentioned or implied)

CONTEXT BLOCKS AVAILABLE:

[Background Event Information]
{background}

[Conversation History]
{conversation}

[User Metadata]
{user_metadata}

[Target Post]
{target_post}

ANALYSIS INSTRUCTIONS:
- Use ONLY information from the non-empty context blocks above
- Do NOT rely on external knowledge or personal assumptions
- If a context field is empty, treat it as unavailable information
- Base your assessments on explicit textual evidence when possible
- For implicit stances, explain your reasoning

QUESTIONS TO ANSWER:

1. POLITICAL IDEOLOGY
   Based on the context, what is the author's political ideology?
   - Left: Progressive/liberal/socialist values
   - Center: Moderate/centrist values
   - Right: Conservative/libertarian values
   
2. STANCE TOWARD POLITICAL FIGURES
   What is the author's stance toward Donald Trump and Joe Biden?
   For each figure mentioned or implied, classify as:
   - favor: Supports/approves of this figure
   - against: Opposes/disapproves of this figure
   - neutral: No clear preference expressed
   - undecided: Insufficient information to determine

CRITICAL: You MUST respond with ONLY valid JSON in the exact format below. Do not include any explanation or text outside the JSON.

RESPONSE FORMAT (MUST BE VALID JSON ONLY):

{{
  "ideology": "Left" or "Center" or "Right",
  "ideology_confidence": <integer 0-100>,
  "stance": "favor" or "against" or "neutral" or "undecided",
  "stance_confidence": <integer 0-100>
}}

Respond with ONLY the JSON object, nothing else:"""


# ============================================================================
# LLM PROVIDER CLASSES
# ============================================================================

class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, model_id: str, temperature: float = 0.7, max_tokens: int = 2048):
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    @abstractmethod
    def query(self, prompt: str) -> Tuple[str, float, Optional[str]]:
        """
        Query the model.
        
        Returns:
            (response_text, raw_confidence_or_probability, any_error)
        """
        pass
    
    def validate_and_repair_response(self, response: str, retry_prompt: Optional[str] = None) -> Tuple[Dict, bool, Optional[str]]:
        """
        Validate response - very lenient, just check if response is not empty.
        
        Returns:
            (parsed_dict, is_valid, error_message)
        """
        if not response or len(response.strip()) < 5:
            error_msg = "Response is empty or too short"
            return {}, False, error_msg
        
        # Try to parse as JSON if it looks like JSON
        if response.strip().startswith('{'):
            try:
                parsed = json.loads(response)
                return parsed, True, None
            except json.JSONDecodeError as e:
                error_msg = f"Invalid JSON format: {str(e)}"
                return {}, False, error_msg
        
        # For non-JSON responses, just check they exist and are reasonable
        return {'raw_text': response}, True, None
    
    def extract_separate_confidences(self, response: str) -> Tuple[Optional[float], Optional[float]]:
        """Extract ideology_confidence and stance_confidence separately. Returns (ideology_conf, stance_conf)."""
        if not response:
            return None, None
            
        ideology_conf = None
        stance_conf = None
        
        # First, try to parse as JSON and extract ideology_confidence or stance_confidence
        try:
            json_response = json.loads(response)
            if 'ideology_confidence' in json_response:
                try:
                    ideology_conf = float(json_response['ideology_confidence'])
                    ideology_conf = min(100, max(0, ideology_conf))
                except (ValueError, TypeError):
                    pass
            if 'stance_confidence' in json_response:
                try:
                    stance_conf = float(json_response['stance_confidence'])
                    stance_conf = min(100, max(0, stance_conf))
                except (ValueError, TypeError):
                    pass
        except (json.JSONDecodeError, ValueError, TypeError):
            pass  # Fall through to pattern matching
        
        # Pattern matching for text-based confidence
        # Look for "Ideology Confidence: X%" and "Stance Confidence: Y%"
        if ideology_conf is None:
            ideology_pattern = r'ideology\s+confidence[:\s]+(\d+(?:\.\d+)?)\s*%'
            match = re.search(ideology_pattern, response, re.IGNORECASE)
            if match:
                try:
                    ideology_conf = float(match.group(1))
                    ideology_conf = min(100, max(0, ideology_conf))
                except ValueError:
                    pass
        
        if stance_conf is None:
            stance_pattern = r'stance\s+confidence[:\s]+(\d+(?:\.\d+)?)\s*%'
            match = re.search(stance_pattern, response, re.IGNORECASE)
            if match:
                try:
                    stance_conf = float(match.group(1))
                    stance_conf = min(100, max(0, stance_conf))
                except ValueError:
                    pass
        
        return ideology_conf, stance_conf

    def extract_confidence(self, response: str) -> Optional[float]:
        """Extract confidence from response text or JSON. Returns average of ideology and stance confidence."""
        ideology_conf, stance_conf = self.extract_separate_confidences(response)
        
        # Return average of both confidences if available
        confidences = []
        if ideology_conf is not None:
            confidences.append(ideology_conf)
        if stance_conf is not None:
            confidences.append(stance_conf)
        
        if confidences:
            return min(100, max(0, sum(confidences) / len(confidences)))
        return None
    
    def extract_prediction(self, response: str, stance_options: List[str]) -> Optional[str]:
        """Extract stance prediction from response."""
        response_lower = response.lower()
        
        for option in stance_options:
            if option.lower() in response_lower:
                return option
        
        # Try to find first mentioned option
        for option in stance_options:
            pattern = r'\b' + re.escape(option.lower()) + r'\b'
            if re.search(pattern, response_lower):
                return option
        
        return None


class OpenAIProvider(LLMProvider):
    """OpenAI API provider (GPT-4, GPT-3.5)."""
    
    def __init__(self, model_id: str, api_key: Optional[str] = None, **kwargs):
        super().__init__(model_id, **kwargs)
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    def query(self, prompt: str) -> Tuple[str, Optional[float], Optional[str]]:
        """Query GPT model via OpenAI API."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            text = response.choices[0].message.content
            confidence = self.extract_confidence(text)
            
            return text, confidence, None
        
        except Exception as e:
            return "", None, str(e)


class AnthropicProvider(LLMProvider):
    """Anthropic API provider (Claude-3 models)."""
    
    def __init__(self, model_id: str, api_key: Optional[str] = None, **kwargs):
        super().__init__(model_id, **kwargs)
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    def query(self, prompt: str) -> Tuple[str, Optional[float], Optional[str]]:
        """Query Claude model via Anthropic API."""
        try:
            response = self.client.messages.create(
                model=self.model_id,
                max_tokens=self.max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            
            text = response.content[0].text
            confidence = self.extract_confidence(text)
            
            return text, confidence, None
        
        except Exception as e:
            return "", None, str(e)


class HuggingFaceProvider(LLMProvider):
    """HuggingFace provider using vLLM for high-performance batch inference."""
    
    def __init__(self, model_id: str, gpu_device: int = 0, tensor_parallel_size: int = 1, **kwargs):
        """
        Initialize HuggingFace provider with vLLM for efficient batch inference.
        
        Args:
            model_id: Model ID from HuggingFace Hub (e.g., "meta-llama/Llama-3.1-8B-Instruct")
            gpu_device: Deprecated - CUDA_VISIBLE_DEVICES should be set globally instead
            tensor_parallel_size: Number of GPUs for tensor parallelism (default: 1)
        """
        super().__init__(model_id, **kwargs)
        self.gpu_device = gpu_device
        self.tensor_parallel_size = tensor_parallel_size
        
        try:
            from vllm import LLM, SamplingParams
            import os
            
            logger.info(f"Loading model {model_id} with vLLM")
            logger.info(f"GPU device: {gpu_device}")
            logger.info(f"Tensor parallel size: {tensor_parallel_size}")
            
            # Set CUDA_VISIBLE_DEVICES for this model
            # For tensor_parallel, we need consecutive GPUs starting from gpu_device
            if tensor_parallel_size > 1:
                gpu_list = list(range(gpu_device, gpu_device + tensor_parallel_size))
                cuda_devices = ','.join(map(str, gpu_list))
            else:
                cuda_devices = str(gpu_device)
            
            os.environ['CUDA_VISIBLE_DEVICES'] = '0,1'
            logger.info(f"Set CUDA_VISIBLE_DEVICES={os.environ['CUDA_VISIBLE_DEVICES']}")
            
            # Initialize vLLM engine - it will use GPUs in CUDA_VISIBLE_DEVICES
            self.llm = LLM(
                model=model_id,
                tensor_parallel_size=2,
                dtype="auto",
                max_model_len=20000,  # Increased to handle longer contexts
                gpu_memory_utilization=0.9,
            )
            
            # Define JSON schema for guided generation
            self.json_schema = {
                "type": "object",
                "properties": {
                    "ideology": {
                        "type": "string",
                        "enum": ["Left", "Center", "Right"]
                    },
                    "ideology_confidence": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "stance": {
                        "type": "string",
                        "enum": ["favor", "against", "neutral", "undecided"]
                    },
                    "stance_confidence": {
                        "type": "integer",
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["ideology", "ideology_confidence", "stance", "stance_confidence"]
            }
            
            # Create sampling params without JSON constraint to avoid vLLM compatibility issues
            self.sampling_params = SamplingParams(
                temperature=self.temperature,
                top_p=0.9,
                max_tokens=self.max_tokens,
            )
            
            logger.info(f"vLLM model loaded successfully")
            
        except ImportError as e:
            raise ImportError(f"vLLM not installed: {e}. Run: pip install vllm")
        except Exception as e:
            raise RuntimeError(f"Failed to load model {model_id} with vLLM: {e}")
    
    def query(self, prompt: str) -> Tuple[str, Optional[float], Optional[str]]:
        """Query single prompt using vLLM."""
        try:
            outputs = self.llm.generate([prompt], self.sampling_params)
            
            if not outputs or len(outputs) == 0:
                return "", None, "No output generated"
            
            output = outputs[0]
            text = output.outputs[0].text.strip()
            
            logger.debug(f"[{self.model_id}] Generated text length: {len(text)} chars")
            
            if len(text) > 0:
                logger.debug(f"[{self.model_id}] Response (first 100 chars): {text[:100]}")
            else:
                logger.warning(f"[{self.model_id}] Response is empty")
            
            confidence = self.extract_confidence(text)
            return text, confidence, None
            
        except Exception as e:
            logger.error(f"[{self.model_id}] vLLM query failed: {type(e).__name__}: {e}")
            return "", None, str(e)
    
    def batch_query(self, prompts: List[str]) -> List[Tuple[str, Optional[float], Optional[str]]]:
        """Batch query multiple prompts efficiently using vLLM."""
        try:
            logger.info(f"[{self.model_id}] Running batch inference on {len(prompts)} prompts...")
            
            outputs = self.llm.generate(prompts, self.sampling_params)
            
            results = []
            for output in outputs:
                text = output.outputs[0].text.strip()
                confidence = self.extract_confidence(text)
                results.append((text, confidence, None))
            
            logger.info(f"[{self.model_id}] Batch inference completed: {len(results)} outputs")
            return results
            
        except Exception as e:
            logger.error(f"[{self.model_id}] Batch query failed: {type(e).__name__}: {e}")
            # Return error for all prompts
            return [("", None, str(e))] * len(prompts)


class InferencePipeline:
    """Manage LLM inference across multiple models and variants."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.models = {}
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize LLM providers from config."""
        for model_config in self.config.get('models', []):
            name = model_config['name']
            provider = model_config['provider']
            model_id = model_config['config']['model_id']
            temperature = model_config['config']['temperature']
            max_tokens = model_config['config']['max_tokens']
            
            if provider == 'openai':
                self.models[name] = OpenAIProvider(
                    model_id, temperature=temperature, max_tokens=max_tokens
                )
            elif provider == 'anthropic':
                self.models[name] = AnthropicProvider(
                    model_id, temperature=temperature, max_tokens=max_tokens
                )
            elif provider == 'huggingface':
                gpu_device = model_config['config'].get('gpu_device', 0)
                tensor_parallel_size = model_config['config'].get('tensor_parallel_size', 1)
                self.models[name] = HuggingFaceProvider(
                    model_id, 
                    gpu_device=gpu_device, 
                    tensor_parallel_size=tensor_parallel_size,
                    temperature=temperature, 
                    max_tokens=max_tokens
                )
    
    def create_prompt(
        self,
        context_text: str,
        target_entity: str,
        stance_options: List[str],
        task_description: str = "Identify the author's political ideology and stance"
    ) -> str:
        """Create standardized prompt from context variant."""
        prompt = f"""You are a political discourse analyst. Your task is to analyze the author's political views based on ONLY the information provided.

{context_text}

ANALYSIS QUESTIONS:

1. POLITICAL IDEOLOGY
   Based ONLY on the information above, what is the author's political ideology?
   Answer Options: Left (progressive/liberal), Center (moderate), Right (conservative/libertarian)
   
2. STANCE TOWARD {target_entity.upper()}
   Based ONLY on the information above, what is the author's stance toward {target_entity}?
   Answer Options: {', '.join(stance_options)}

RESPONSE FORMAT:
Please provide your answer in this exact format:

Ideology: [Left/Center/Right]
Ideology Confidence: [0-100]%

{target_entity} Stance: [one of the options]
Stance Confidence: [0-100]%

Brief Reasoning: [1-2 sentences explaining your assessment]"""
        
        return prompt
    
    def query_model(
        self,
        model_name: str,
        prompt: str,
        retries: int = 3,
        retry_delay: float = 2.0
    ) -> Dict:
        """Query a single model with validation and retries."""
        if model_name not in self.models:
            return {
                'model': model_name,
                'success': False,
                'error': f'Model {model_name} not initialized',
            }
        
        model = self.models[model_name]
        validation_attempts = 0
        max_validation_retries = 3
        
        for attempt in range(retries):
            try:
                response_text, confidence, error = model.query(prompt)
                
                if error:
                    if attempt < retries - 1:
                        time.sleep(retry_delay)
                        continue
                    return {
                        'model': model_name,
                        'success': False,
                        'error': error,
                    }
                
                # Validate response format
                parsed_response, is_valid, validation_error = model.validate_and_repair_response(response_text)
                
                if not is_valid:
                    validation_attempts += 1
                    logger.warning(f"[{model_name}] Validation failed (attempt {validation_attempts}/{max_validation_retries}): {validation_error}")
                    
                    if validation_attempts < max_validation_retries:
                        # Generate retry prompt with error feedback
                        retry_prompt = f"""{prompt}

IMPORTANT - Your previous response had the following issue:
ERROR: {validation_error}

Please provide a corrected response in the exact JSON format specified above.
Ensure your response is valid JSON that can be parsed."""
                        
                        logger.info(f"[{model_name}] Retrying with error feedback...")
                        response_text, confidence, error = model.query(retry_prompt)
                        
                        if not error:
                            parsed_response, is_valid, validation_error = model.validate_and_repair_response(response_text)
                            if is_valid:
                                logger.info(f"[{model_name}] Validation succeeded on retry {validation_attempts}")
                                return {
                                    'model': model_name,
                                    'success': True,
                                    'response_text': response_text,
                                    'confidence': confidence,
                                    'attempt': attempt + 1,
                                    'validation_attempts': validation_attempts,
                                    'parsed_response': parsed_response,
                                }
                            continue
                    else:
                        logger.error(f"[{model_name}] Max validation retries exceeded. Final error: {validation_error}")
                        return {
                            'model': model_name,
                            'success': False,
                            'error': f"Validation failed after {max_validation_retries} attempts: {validation_error}",
                            'raw_response': response_text,
                        }
                
                # Validation passed
                return {
                    'model': model_name,
                    'success': True,
                    'response_text': response_text,
                    'confidence': confidence,
                    'attempt': attempt + 1,
                    'validation_attempts': validation_attempts,
                    'parsed_response': parsed_response,
                }
            
            except Exception as e:
                logger.error(f"[{model_name}] Query error: {str(e)}")
                if attempt < retries - 1:
                    time.sleep(retry_delay)
                    continue
                return {
                    'model': model_name,
                    'success': False,
                    'error': str(e),
                }
        
        return {
            'model': model_name,
            'success': False,
            'error': 'Max retries exceeded',
        }
    
    def query_all_models(
        self,
        prompt: str,
        retries: int = 3,
        retry_delay: float = 2.0
    ) -> Dict[str, Dict]:
        """Query all initialized models."""
        results = {}
        
        for model_name in self.models.keys():
            result = self.query_model(model_name, prompt, retries, retry_delay)
            results[model_name] = result
        
        return results
    
    def batch_query_all_models(
        self,
        prompts: List[str],
        retries: int = 3,
    ) -> List[Dict[str, Dict]]:
        """
        Batch query all models with multiple prompts.
        
        Args:
            prompts: List of prompts to process
            retries: Number of retries for failed queries
            
        Returns:
            List of results dicts, one per prompt. Each dict maps model_name -> result.
        """
        # Initialize results structure
        batch_results = [{} for _ in range(len(prompts))]
        
        for model_name, model in self.models.items():
            logger.info(f"[{model_name}] Processing batch of {len(prompts)} prompts...")
            
            # Check if model supports batch inference (vLLM)
            if hasattr(model, 'batch_query'):
                try:
                    # Use batch inference
                    batch_outputs = model.batch_query(prompts)
                    
                    # Process each output
                    for i, (text, confidence, error) in enumerate(batch_outputs):
                        if error:
                            batch_results[i][model_name] = {
                                'model': model_name,
                                'success': False,
                                'error': error,
                            }
                        else:
                            # Validate response
                            parsed_response, is_valid, validation_error = model.validate_and_repair_response(text)
                            
                            batch_results[i][model_name] = {
                                'model': model_name,
                                'success': is_valid,
                                'response_text': text,
                                'confidence': confidence,
                                'parsed_response': parsed_response if is_valid else None,
                                'error': validation_error if not is_valid else None,
                            }
                    
                except Exception as e:
                    logger.error(f"[{model_name}] Batch query failed: {e}")
                    # Mark all as failed
                    for i in range(len(prompts)):
                        batch_results[i][model_name] = {
                            'model': model_name,
                            'success': False,
                            'error': str(e),
                        }
            else:
                # Fallback to sequential queries
                logger.info(f"[{model_name}] Model doesn't support batch inference, using sequential queries...")
                for i, prompt in enumerate(prompts):
                    result = self.query_model(model_name, prompt, retries=retries)
                    batch_results[i][model_name] = result
        
        return batch_results
    
    def evaluate_sample(
        self,
        sample_id: str,
        context_variants: Dict[str, str],
        target_entity: str,
        stance_options: List[str],
        ground_truth_label: Optional[str] = None,
        confidence_only: bool = False,
        response_logger = None,
    ) -> Dict:
        """
        Evaluate a single sample across all models and context variants.
        
        Returns comprehensive evaluation results.
        If confidence_only=True, only records confidence values per variant/model.
        
        Args:
            response_logger: Optional callback to log responses to JSONL
        """
        results = {
            'sample_id': sample_id,
            'target_entity': target_entity,
            'ground_truth': ground_truth_label,
            'variants': {},
        }
        
        for variant_name, context_text in context_variants.items():
            prompt = self.create_prompt(
                context_text, target_entity, stance_options
            )
            
            model_results = self.query_all_models(prompt)
            
            # Log each model response to JSONL
            if response_logger:
                for model_name, model_result in model_results.items():
                    # Extract separate confidences
                    response_text = model_result.get('response_text', '')
                    provider = self.models[model_name]
                    ideology_conf, stance_conf = provider.extract_separate_confidences(response_text)
                    
                    response_logger({
                        'timestamp': time.time(),
                        'sample_id': sample_id,
                        'variant': variant_name,
                        'model': model_name,
                        'prompt': prompt,
                        'response': response_text,
                        'ideology_confidence': ideology_conf,
                        'stance_confidence': stance_conf,
                        'confidence': model_result.get('confidence'),
                        'success': model_result.get('success', False),
                        'error': model_result.get('error'),
                    })
            
            if confidence_only:
                # Only record confidence per model
                confidence_results = {}
                for model_name, model_result in model_results.items():
                    confidence_results[model_name] = {
                        'confidence': model_result.get('confidence'),
                        'success': model_result.get('success', False)
                    }
                results['variants'][variant_name] = confidence_results
            else:
                # Full results
                results['variants'][variant_name] = {
                    'prompt': prompt,
                    'model_results': model_results,
                }
        
        return results


class BatchEvaluator:
    """Batch evaluation of multiple samples."""
    
    def __init__(self, pipeline: InferencePipeline, cache_dir: str = "./cache", responses_jsonl: Optional[str] = None):
        self.pipeline = pipeline
        self.cache_dir = cache_dir
        self.responses_jsonl = responses_jsonl
        os.makedirs(cache_dir, exist_ok=True)
        
        # Initialize JSONL file for responses
        if self.responses_jsonl:
            Path(self.responses_jsonl).parent.mkdir(parents=True, exist_ok=True)
            # Clear previous file if exists
            if Path(self.responses_jsonl).exists():
                Path(self.responses_jsonl).unlink()
    
    def _log_response_to_jsonl(self, response_record: Dict):
        """Log a single model response to JSONL file."""
        if not self.responses_jsonl:
            return
        
        try:
            with open(self.responses_jsonl, 'a') as f:
                f.write(json.dumps(response_record, default=str) + '\n')
        except Exception as e:
            logger.warning(f"Failed to write to JSONL: {e}")
    
    def evaluate_batch(
        self,
        samples: List[Dict],
        target_entity: str,
        stance_options: List[str],
        save_interval: int = 10,
        output_file: Optional[str] = None,
        confidence_only: bool = False,
        batch_size: int = 32,  # Process 32 prompts at a time
    ) -> List[Dict]:
        """
        Evaluate batch of samples using efficient batch inference.
        
        Args:
            samples: List of sample dicts with:
                - sample_id
                - context_variants (dict of variant_name -> context_text)
                - ground_truth (optional label)
            target_entity: Entity to assess stance toward
            stance_options: Possible stance categories
            save_interval: Save results every N samples
            output_file: File to save results
            confidence_only: Only record confidence, skip full predictions
            batch_size: Number of prompts to process in parallel (default: 32)
        
        Returns:
            List of evaluation results
        """
        # Get variant names (assume all samples have same variants)
        if not samples:
            return []
        
        variant_names = list(samples[0].get('context_variants', {}).keys())
        logger.info(f"Processing {len(samples)} samples with {len(variant_names)} variants each")
        logger.info(f"Variants: {', '.join(variant_names)}")
        logger.info(f"Using batch size: {batch_size}")
        
        # Pre-initialize results structure for all samples
        all_results = []
        for i, sample in enumerate(samples):
            all_results.append({
                'sample_id': sample.get('sample_id'),
                'target_entity': target_entity,
                'ground_truth': sample.get('ground_truth'),
                'variants': {},
            })
        
        # Process by variant to maximize batching efficiency
        for variant_name in variant_names:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing variant: {variant_name}")
            logger.info(f"{'='*60}")
            
            # Prepare all prompts for this variant
            variant_prompts = []
            sample_indices = []
            
            for i, sample in enumerate(samples):
                context_text = sample.get('context_variants', {}).get(variant_name, '')
                if context_text:
                    prompt = self.pipeline.create_prompt(
                        context_text, target_entity, stance_options
                    )
                    variant_prompts.append(prompt)
                    sample_indices.append(i)
            
            logger.info(f"Generated {len(variant_prompts)} prompts for variant {variant_name}")
            
            # Process in batches
            for batch_start in range(0, len(variant_prompts), batch_size):
                batch_end = min(batch_start + batch_size, len(variant_prompts))
                batch_prompts = variant_prompts[batch_start:batch_end]
                batch_indices = sample_indices[batch_start:batch_end]
                
                logger.info(f"Processing batch {batch_start//batch_size + 1}/{(len(variant_prompts)-1)//batch_size + 1} ({len(batch_prompts)} prompts)...")
                
                # Batch query all models
                batch_model_results = self.pipeline.batch_query_all_models(batch_prompts)
                
                # Store results for each sample in this batch
                for local_idx, (prompt, global_idx) in enumerate(zip(batch_prompts, batch_indices)):
                    sample = samples[global_idx]
                    model_results = batch_model_results[local_idx]
                    
                    # Log each model response to JSONL
                    for model_name, model_result in model_results.items():
                        response_text = model_result.get('response_text', '')
                        provider = self.pipeline.models[model_name]
                        ideology_conf, stance_conf = provider.extract_separate_confidences(response_text)
                        
                        self._log_response_to_jsonl({
                            'timestamp': time.time(),
                            'sample_id': sample.get('sample_id'),
                            'variant': variant_name,
                            'model': model_name,
                            'prompt': prompt,
                            'response': response_text,
                            'ideology_confidence': ideology_conf,
                            'stance_confidence': stance_conf,
                            'confidence': model_result.get('confidence'),
                            'success': model_result.get('success', False),
                            'error': model_result.get('error'),
                        })
                    
                    # Store results
                    if confidence_only:
                        confidence_results = {}
                        for model_name, model_result in model_results.items():
                            confidence_results[model_name] = {
                                'confidence': model_result.get('confidence'),
                                'success': model_result.get('success', False)
                            }
                        all_results[global_idx]['variants'][variant_name] = confidence_results
                    else:
                        all_results[global_idx]['variants'][variant_name] = {
                            'prompt': prompt,
                            'model_results': model_results,
                        }
                
                # Save intermediate results
                if (batch_end) % save_interval == 0 or batch_end == len(variant_prompts):
                    logger.info(f"Processed {batch_end}/{len(variant_prompts)} prompts for {variant_name}...")
                    if output_file:
                        with open(output_file, 'w') as f:
                            json.dump(all_results, f, indent=2, default=str)
        
        # Final save
        logger.info(f"\nCompleted all {len(samples)} samples!")
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(all_results, f, indent=2, default=str)
        
        return all_results


if __name__ == "__main__":
    # Example usage
    config = {
        'models': [
            {
                'name': 'gpt-4',
                'provider': 'openai',
                'config': {
                    'model_id': 'gpt-4-turbo-preview',
                    'temperature': 0.7,
                    'max_tokens': 256
                }
            }
        ]
    }
    
    pipeline = InferencePipeline(config)
    
    # Example prompt
    prompt = """
    Identify the author's stance toward gun control.
    
    [TARGET POST]
    "We need sensible gun regulations to keep our communities safe."
    
    Question: What is the author's stance toward gun control?
    Please respond with:
    1. Your answer (one of: strongly support, support, neutral, oppose, strongly oppose)
    2. Your confidence level (0-100%)
    3. Brief reasoning
    """
    
    result = pipeline.query_model('gpt-4', prompt)
    print(json.dumps(result, indent=2))
