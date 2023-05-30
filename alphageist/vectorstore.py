import os
import logging
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.embeddings.base import Embeddings
from langchain.vectorstores.chroma import Chroma
from alphageist.doc_generator import get_docs_from_path
from alphageist.errors import MissingConfigComponentError
from alphageist import util
import alphageist.config as cfg


def vectorstore_exists(persist_directory: str) -> bool:
    return os.path.exists(persist_directory)


def get_embeddings(config: dict) -> Embeddings:
    """This method should return the proper Embeddings according
    to the config"""
    if not cfg.API_KEY_OPEN_AI in config.keys():
        raise MissingConfigComponentError(cfg.API_KEY_OPEN_AI)
    return OpenAIEmbeddings(openai_api_key=config[cfg.API_KEY_OPEN_AI])


def load_vectorstore(config: dict) -> Chroma:
    embedding = get_embeddings(config)
    if not cfg.VECTORDB_DIR in config:
        raise MissingConfigComponentError(cfg.VECTORDB_DIR)
    vector_db_dir = config[cfg.VECTORDB_DIR]
    if not vector_db_dir:
        raise ValueError("No directory provided for persisting db")
    if not util.path_is_valid_format(vector_db_dir):
        raise ValueError("{vector_db_dir} is not a valid directory")

    logging.info(f"Loading vectorestore from {vector_db_dir}...")
    client = Chroma(embedding_function=embedding,
                    persist_directory=config[cfg.VECTORDB_DIR])
    return client


def create_vectorstore(config: dict) -> Chroma:
    if not cfg.SEARCH_DIRS in config.keys():
        raise MissingConfigComponentError(cfg.SEARCH_DIRS)

    search_dir = config[cfg.SEARCH_DIRS]
    if not util.path_is_valid_format(search_dir):
        raise ValueError(f"{search_dir} is not a valid directory")

    docs = get_docs_from_path(search_dir)

    if not docs:
        raise ValueError(f"No supported files found in {search_dir}")

    if not cfg.VECTORDB_DIR in config.keys():
        raise MissingConfigComponentError(cfg.VECTORDB_DIR)
    vector_db_dir = config[cfg.VECTORDB_DIR]
    if not vector_db_dir:
        raise ValueError(f"Path for persisting db can not be empty")
    if not util.path_is_valid_format(vector_db_dir):
        raise ValueError(f'"{vector_db_dir}" is not a valid directory')

    embedding = get_embeddings(config)
    logging.info(f"Creating vectorstore...")
    client = Chroma.from_documents(docs, embedding=embedding, persist_directory=vector_db_dir)
    logging.info(f"Saving vectorstore to {vector_db_dir}")
    client.persist() # Save DB
    return client
