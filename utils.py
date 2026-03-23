import os
import yaml

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
    


def load_pdf(file_path: str, chunck_size: int = 32000, image_ocr: bool = False) -> tuple[str, list[str]]:
    if image_ocr:
        loader = PyMuPDF4LLMLoader(file_path, mode="single")
    else:
        loader = PyMuPDF4LLMLoader(file_path, 
                                   mode="single",
                                   extract_images=True, 
                                   images_parser=TesseractBlobParser())
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunck_size, chunk_overlap=0)
    
    title = loader.load()[0].metadata["title"] if "title" in loader.load()[0].metadata else ""
    content = loader.load()[0].page_content

    return title, splitter.split_text(content)