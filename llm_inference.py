"""
LLM inference pipeline for context experiment.

Supports: OpenAI (GPT-4, GPT-3.5), Anthropic (Claude), and HuggingFace models.
"""

import os
import json
import time
from typing import Dict, List, Tuple, Optional
from abc import ABC, abstractmethod
import re


class LLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, model_id: str, temperature: float = 0.7, max_tokens: int = 256):
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
    
    def extract_confidence(self, response: str) -> Optional[float]:
        """Extract confidence from response text."""
        # Look for patterns like "Confidence: 85%", "confidence (0-100): 85", etc.
        patterns = [
            r'confidence[:\s]*(\d+)\s*%?',
            r'(\d+)\s*%\s*(?:confident|confidence)',
            r'confidence[:\s]*(\d+(?:\.\d+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                conf_value = float(match.group(1))
                # Normalize to 0-100 if it's 0-1
                if conf_value <= 1:
                    conf_value = conf_value * 100
                return min(100, max(0, conf_value))
        
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
    """HuggingFace provider (via Replicate or local deployment)."""
    
    def __init__(self, model_id: str, use_replicate: bool = True, **kwargs):
        super().__init__(model_id, **kwargs)
        self.use_replicate = use_replicate
        
        if use_replicate:
            import replicate
            self.replicate_client = replicate
        else:
            try:
                from transformers import pipeline
                self.pipeline = pipeline(
                    "text-generation",
                    model=model_id,
                    device=0  # GPU device 0
                )
            except ImportError:
                raise ImportError("transformers package not installed. Run: pip install transformers torch")
    
    def query(self, prompt: str) -> Tuple[str, Optional[float], Optional[str]]:
        """Query HuggingFace model."""
        try:
            if self.use_replicate:
                return self._query_replicate(prompt)
            else:
                return self._query_local(prompt)
        except Exception as e:
            return "", None, str(e)
    
    def _query_replicate(self, prompt: str) -> Tuple[str, Optional[float], Optional[str]]:
        """Query via Replicate API."""
        try:
            output = self.replicate_client.run(
                self.model_id,
                input={"prompt": prompt}
            )
            text = "".join(output) if isinstance(output, list) else output
            confidence = self.extract_confidence(text)
            return text, confidence, None
        except Exception as e:
            return "", None, str(e)
    
    def _query_local(self, prompt: str) -> Tuple[str, Optional[float], Optional[str]]:
        """Query local HuggingFace model."""
        try:
            output = self.pipeline(
                prompt,
                max_length=self.max_tokens,
                temperature=self.temperature,
                do_sample=True,
            )
            text = output[0]['generated_text']
            confidence = self.extract_confidence(text)
            return text, confidence, None
        except Exception as e:
            return "", None, str(e)


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
                self.models[name] = HuggingFaceProvider(
                    model_id, temperature=temperature, max_tokens=max_tokens
                )
    
    def create_prompt(
        self,
        context_text: str,
        target_entity: str,
        stance_options: List[str],
        task_description: str = "Identify the author's stance"
    ) -> str:
        """Create standardized prompt from context variant."""
        prompt = f"""{task_description} toward {target_entity}.

{context_text}

Question: What is the author's stance toward {target_entity}?

Please respond with:
1. Your answer (one of: {', '.join(stance_options)})
2. Your confidence level (0-100%)
3. Brief reasoning"""
        
        return prompt
    
    def query_model(
        self,
        model_name: str,
        prompt: str,
        retries: int = 3,
        retry_delay: float = 2.0
    ) -> Dict:
        """Query a single model with retries."""
        if model_name not in self.models:
            return {
                'model': model_name,
                'success': False,
                'error': f'Model {model_name} not initialized',
            }
        
        model = self.models[model_name]
        
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
                
                return {
                    'model': model_name,
                    'success': True,
                    'response_text': response_text,
                    'confidence': confidence,
                    'attempt': attempt + 1,
                }
            
            except Exception as e:
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
    
    def evaluate_sample(
        self,
        sample_id: str,
        context_variants: Dict[str, str],
        target_entity: str,
        stance_options: List[str],
        ground_truth_label: Optional[str] = None,
    ) -> Dict:
        """
        Evaluate a single sample across all models and context variants.
        
        Returns comprehensive evaluation results.
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
            results['variants'][variant_name] = {
                'prompt': prompt,
                'model_results': model_results,
            }
        
        return results


class BatchEvaluator:
    """Batch evaluation of multiple samples."""
    
    def __init__(self, pipeline: InferencePipeline, cache_dir: str = "./cache"):
        self.pipeline = pipeline
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def evaluate_batch(
        self,
        samples: List[Dict],
        target_entity: str,
        stance_options: List[str],
        save_interval: int = 10,
        output_file: Optional[str] = None
    ) -> List[Dict]:
        """
        Evaluate batch of samples.
        
        Args:
            samples: List of sample dicts with:
                - sample_id
                - context_variants (dict of variant_name -> context_text)
                - ground_truth (optional label)
            target_entity: Entity to assess stance toward
            stance_options: Possible stance categories
            save_interval: Save results every N samples
            output_file: File to save results
        
        Returns:
            List of evaluation results
        """
        all_results = []
        
        for i, sample in enumerate(samples):
            result = self.pipeline.evaluate_sample(
                sample_id=sample.get('sample_id'),
                context_variants=sample.get('context_variants', {}),
                target_entity=target_entity,
                stance_options=stance_options,
                ground_truth_label=sample.get('ground_truth'),
            )
            
            all_results.append(result)
            
            # Save intermediate results
            if (i + 1) % save_interval == 0:
                print(f"Processed {i + 1} samples...")
                if output_file:
                    with open(output_file, 'w') as f:
                        json.dump(all_results, f, indent=2)
        
        # Final save
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(all_results, f, indent=2)
        
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
