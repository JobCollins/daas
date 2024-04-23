from langchain.chat_models import ChatOpenAI
from langchain_community.llms import Ollama
from langchain_community.chat_models import ChatOllama


from constants import chat_openai_model_kwargs, langchain_chat_kwargs


# Optional, set the API key for OpenAI if it's not set in the environment.
# os.environ["OPENAI_API_KEY"] = "xxxxxx"


def get_chat_openai(model_name):
    """
    Returns an instance of the ChatOpenAI class initialized with the specified model name.

    Args:
        model_name (str): The name of the model to use.

    Returns:
        ChatOpenAI: An instance of the ChatOpenAI class.

    """
    # add local llm implementation
    if model_name.startswith("gpt"):
        llm = ChatOpenAI(
            model_name=model_name,
            model_kwargs=chat_openai_model_kwargs,
            **langchain_chat_kwargs
        )
    else:
        llm = ChatOllama(
            model_name = model_name,
            **langchain_chat_kwargs
        )
    return llm
