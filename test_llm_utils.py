import os
import yaml
from llm_utils import generate_completion

def test_generate_completion():
    # Load config to get the environment variable name
    with open('models.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Get the first environment variable name
    env_var_name = list(config['models'][0].keys())[0]
    
    # Get API key from environment variable
    api_key = os.getenv(env_var_name)
    if not api_key:
        raise ValueError(f"Please set {env_var_name} environment variable")
    
    # Test prompt
    test_prompt = "What is 2+2? Answer in one word."
    
    try:
        # Test with explicit API key
        response = generate_completion(test_prompt, api_key)
        print(f"Test prompt: {test_prompt}")
        print(f"Response with explicit API key: {response}")
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Test with environment variable
        response = generate_completion(test_prompt)
        print(f"Response with environment variable: {response}")
        assert isinstance(response, str)
        assert len(response) > 0
        
        print("Test passed successfully!")
    except Exception as e:
        print(f"Test failed with error: {str(e)}")

if __name__ == "__main__":
    test_generate_completion() 