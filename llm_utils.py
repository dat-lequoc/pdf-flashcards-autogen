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

    # Get the correct environment variable for the model.
    env_var = model_to_env.get(model)
    if not env_var:
        raise ValueError(f"Model '{model}' is not supported. Available models: {list(model_to_env.keys())}")

    # First, check if the environment variable is set.
    env_api_key = os.getenv(env_var)
    if env_api_key:
        # Use the API key from environment if available
        api_key = env_api_key
    elif api_key:
        # Fallback to the API key provided by the user
        pass
    else:
        raise ValueError(f"Please set {env_var} environment variable or provide the API key.")

    messages = [{"role": "user", "content": prompt}]
    
    response = completion(
        model=model,
        messages=messages,
        api_key=api_key
    )
    
    return response.choices[0].message.content 