from litellm import completion
import yaml
import os

def load_model_config():
    with open('models.yaml', 'r') as file:
        return yaml.safe_load(file)

def generate_completion(prompt: str, model: str = None, api_key: str = None) -> str:
    """
    Generate completion using LiteLLM with the configured model.
    
    Args:
        prompt (str): The input prompt.
        model (str, optional): The model to use (if not provided, default is used).
        api_key (str, optional): Override API key. If not provided, will use environment variable.
        
    Returns:
        str: The generated completion text.
    """
    config = load_model_config()

    # Build a mapping of model to the required API key environment variable.
    model_to_env = {}
    for item in config['models']:
        for env_key, models in item.items():
            for m in models:
                model_to_env[m] = env_key

    # Use the default model from the first configuration if none provided.
    if model is None:
        first_env_var = list(config['models'][0].keys())[0]
        model = config['models'][0][first_env_var][0]

    env_var = model_to_env.get(model)
    if not env_var:
        raise ValueError("Model is not supported.")

    if api_key is None:
        api_key = os.getenv(env_var)
    if not api_key:
        raise ValueError(f"Please set {env_var} environment variable")
    
    messages = [{"role": "user", "content": prompt}]
    
    response = completion(
        model=model,
        messages=messages,
        api_key=api_key
    )
    
    return response.choices[0].message.content 