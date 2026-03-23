import os
import yaml
from re import search, MULTILINE

from langchain.chat_models import BaseChatModel, init_chat_model
from langchain.embeddings import Embeddings, init_embeddings
from langchain_pymupdf4llm import PyMuPDF4LLMLoader
from langchain_community.document_loaders.parsers import TesseractBlobParser
from langchain_text_splitters import RecursiveCharacterTextSplitter



def get_llm_instance(lm_type:str, embedding=False) -> BaseChatModel | Embeddings: 
    with open("lm-config.yaml", "r") as in_file:
        lm_config = yaml.safe_load(in_file)
    
    lm_info = lm_config[lm_type]

    model = lm_info.pop("model")
    provider = lm_info.pop("provider")
    key = lm_info.pop("key")

    if key:
        print(f"{provider.upper()}_API_KEY")
        os.environ[f"{provider.upper()}_API_KEY"] = key

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


def load_pdf(file_path: str, chunck_size: int = 32000, image_ocr: bool = False) -> tuple[str, list[str]]:
    if image_ocr:
        loader = PyMuPDF4LLMLoader(file_path, mode="single")
    else:
        loader = PyMuPDF4LLMLoader(file_path, 
                                   mode="single",
                                   extract_images=True, 
                                   images_parser=TesseractBlobParser())
    
    content = loader.load()[0].page_content
    title = loader.load()[0].metadata["title"]  

    if not title:
        md_title = get_first_title(content)
        title = md_title if md_title else file_path.split("/")[-1].replace(".pdf", "")


    splitter = RecursiveCharacterTextSplitter(chunk_size=chunck_size, chunk_overlap=0)
    return title, splitter.split_text(content)