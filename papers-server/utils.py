import os
import yaml
from re import search, MULTILINE

from langchain.chat_models import BaseChatModel, init_chat_model
from langchain.embeddings import Embeddings, init_embeddings
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


CONFIG_FILE = os.environ['LM_CONFIG_FILE']

def get_llm_instance(lm_type:str, embedding=False) -> BaseChatModel | Embeddings: 
    with open(CONFIG_FILE, "r") as in_file:
        lm_config = yaml.safe_load(in_file)
    
    lm_info = lm_config[lm_type]

    model = lm_info.pop("model")
    provider = lm_info.pop("provider")
    key = lm_info.pop("key")
    key_env_var = lm_info.pop("key_env_var")

    if key:
        key_env_var = key_env_var if key_env_var else f"{provider.upper()}_API_KEY"
        os.environ[key_env_var] = key

    if embedding:
        return init_embeddings(model=model, provider=provider, **lm_info)
    else:
        return init_chat_model(model=model, model_provider=provider, **lm_info)


# So that Pylance will stop complaining
def get_chat(lm_type: str) -> BaseChatModel:
    return get_llm_instance(lm_type=lm_type, embedding=False)

def get_embedding(lm_type: str) -> Embeddings:
    return get_llm_instance(lm_type=lm_type, embedding=True)



def get_first_title(md_text: str) -> str:
    match = search(r'^(#{1,6})\s+(.*)', md_text, MULTILINE)
    if match:
        return match.group(2).strip()
    return ""


def load_pdf(file_path: str, chunk_size: int = 2048) -> tuple[str, list[str] | str, dict]:
    loader = PyMuPDF4LLMLoader(
        file_path, mode="single",
        table_strategy="text",
        pages_delimiter=" ")
    
    content = loader.load()[0].page_content
    title = loader.load()[0].metadata["title"]  

    if not title:
        md_title = get_first_title(content)
        title = md_title if md_title else file_path.split("/")[-1].replace(".pdf", "")

    if chunk_size > 0:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_size//10)
        return title, splitter.split_text(content), loader.load()[0].metadata
    else:
        return title, content, loader.load()[0].metadata