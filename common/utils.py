import os
import yaml
from re import search, MULTILINE, compile, sub

import pymupdf.layout

from langchain.chat_models import BaseChatModel, init_chat_model
from langchain.embeddings import Embeddings, init_embeddings
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

#LLM INSTANCING
CONFIG_FILE = os.environ['LM_CONFIG_FILE']
TOKEN_CHAR_RATIO = 1/1.5

def count_tokens(text: str) -> int:
    return len(text)*TOKEN_CHAR_RATIO

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



# PDF LOADING AND CHUNKING
def strip_markdown_tables(content: str) -> str:
    table_pattern = compile(
        r"^\s*\|.*\|.*\n"           # Header row
        r"^\s*\|[\s\-:|]+\|\s*\n"   # Separator row
        r"(^\s*\|.*\|.*\n?)*",      # Body rows
        MULTILINE
    )
    return sub(table_pattern, "", content)

def remove_multi_line_breaks(content: str) -> str:
    return sub(r"[\n]+", "\n", content)

def remove_links(content: str) -> str:
    content = sub(r"\(https?://\S+\)", "", content)
    content = sub(r"\[https?://\S+\]", "", content)
    content = sub(r"www\.\S+", "", content)
    return sub(r"https://\S+", "", content)

def remove_references(content: str) -> str:
    if "References" in content:
        return "References".join(content.split("References")[:-1])
    else:
        return content

def clean_content(content: str, extract_tables: bool = False) -> str:
    functions = [
        remove_multi_line_breaks,
        remove_links,
        remove_references
    ]
    if not extract_tables:
        functions.insert(0, strip_markdown_tables)
    for function in functions:
        content = function(content)
    return content

def get_first_title(md_text: str) -> str:
    match = search(r'^(#{1,6})\s+(.*)', md_text, MULTILINE)
    if match:
        return match.group(2).strip()
    return ""

def load_pdf(file_path: str) -> tuple[str, list[str] | str, dict]:
    loader = PyMuPDF4LLMLoader(
        file_path,
        extract_images=False,
        mode="single",
        pages_delimiter=" ")
    
    content = loader.load()[0].page_content
    title = loader.load()[0].metadata["title"]
    
    if not title:
        md_title = get_first_title(content)
        title = md_title if md_title else file_path.split("/")[-1].replace(".pdf", "")

    return title, content, loader.load()[0].metadata


def split_document(document: str,
                   chunk_size: int = 2048,
                   overlap: float = 0.1,
                   clean_document= True
                  ) -> tuple[list[str], list[int]]:
    
    splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            length_function=count_tokens,
            chunk_overlap=int(chunk_size*overlap))

    document = clean_content(document) if clean_document else document
    
    chunks = splitter.split_text(document)
    centers = []
    chunks_sum = 0
    for chunk in chunks:
        centers.append(chunks_sum + len(chunk)//2)
        chunks_sum += len(chunk)
    return chunks, centers
    
