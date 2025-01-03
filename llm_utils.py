from litellm import completion
import yaml
import os

def load_model_config():
    with open('models.yaml', 'r') as file:
        return yaml.safe_load(file)

def generate_completion(prompt: str, api_key: str = None) -> str:
    """
    Generate completion using LiteLLM with the configured model
    
    Args:
        prompt (str): The input prompt
        api_key (str, optional): Override API key. If not provided, will use environment variable
        
    Returns:
        str: The generated completion text
    """
    config = load_model_config()
    
    # Get the first environment variable and its models
    first_env_var = list(config['models'][0].keys())[0]
    model_name = config['models'][0][first_env_var][0]
    
    # If no API key provided, get from environment
    if api_key is None:
        api_key = os.getenv(first_env_var)
        if not api_key:
            raise ValueError(f"Please set {first_env_var} environment variable")
    
    messages = [{"role": "user", "content": prompt}]
    
    response = completion(
        model=model_name,
        messages=messages,
        api_key=api_key
    )
    
    return response.choices[0].message.content 