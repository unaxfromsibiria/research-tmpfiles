import os.path
import re
from collections import defaultdict
from time import monotonic
from typing import Dict
from typing import Iterable
from typing import List
from typing import Union

from sentence_transformers import SentenceTransformer
from sqlalchemy import delete as sql_delete
from sqlalchemy import func
from sqlalchemy import select
from sqlalchemy import update as sql_update
from sqlalchemy.orm import Session

from .db import current_engine
from .models import VEC_DIMENSIONS
from .models import DataStorageModel
from .models import now
from .settings import ServerSettings

sentence_spliter = re.compile(r"[.!?;] +")
space_comma_splitter = re.compile(r"[\s,]+")
word_regex = re.compile(r"\S+")

part_sep = ", "
prompt_pr = {}
service_state = {
    "settings": None,
    "engine": None,
    "model": None,
}


def result_token_count(data: Dict[str, List[Dict[str, Union[str, float]]]]) -> int:
    """
    Calculate the total number of tokens in the given data.

    Args:
        data (Dict[str, List[Dict[str, Union[str, float]]]]): The input data containing documents and their respective items with scores.
    Returns:
        int: Total token count across all documents.
    """
    return sum(
        sum(1 for _ in word_regex.finditer(item.get("data") or ""))
        for items in data.values() for item in items
    )


def drop_low_rate_chunk(data: Dict[str, List[Dict[str, Union[str, float]]]]) -> None:
    """
    Remove the chunk with the lowest score from the given data.

    This function sorts all chunks by their combined scores (l2 and cosine) and removes the one with the lowest score.
    If multiple chunks have the same score, it removes the first one encountered.

    Args:
        data (Dict[str, List[Dict[str, Union[str, float]]]]): The input data containing documents and their respective items with scores.
    """
    index_chunk_size = []
    for d_name, items in data.items():
        for index, item in enumerate(items):
            score = int((item["l2"] + item["cosine"]) * 1000)
            index_chunk_size.append((score, item["l2"], item["cosine"], index, d_name))

    if index_chunk_size:
        index_chunk_size.sort(reverse=True)
        (*_, index, doc_name), *_ = index_chunk_size
        del data[doc_name][index]


def preapare_state(settings: ServerSettings = ServerSettings()):
    """
    Prepare the service state by initializing settings and engine.
    """
    if service_state.get("settings"):
        return

    service_state["settings"] = settings
    service_state["engine"] = current_engine(settings=settings)


def split_text(text: str, chunk_size: int = 200, tolerance: float = 0.1) -> Iterable[str]:
    """Splits text into sentences based on punctuation marks"""
    if not 0.01 < tolerance <= 0.5:
        raise ValueError("Incorrect value tolerance (must be between 0.1% and 50%)")

    delta = tolerance * chunk_size
    parts = sentence_spliter.split(text)
    chunk = []
    current_chunk_size = 0

    for index, part in enumerate(parts):
        if not part:
            continue

        if index >= len(parts) - 1:
            part = part.strip(".")

        words = " ".join(
            filter(None, (word.strip() for word in space_comma_splitter.split(part)))
        )
        diff = abs(current_chunk_size - chunk_size)
        if current_chunk_size and diff <= delta or current_chunk_size > chunk_size:
            yield part_sep.join(chunk)
            chunk.clear()
            current_chunk_size = 0

        current_chunk_size += len(words)
        chunk.append(words)

    if chunk:
        yield part_sep.join(chunk)


def add_document_content_to_storage(document_name: str, content: str, refresh: bool = False) -> str:
    """
    Adds a document to the storage by reading its content, splitting it into chunks,
    and saving each chunk as an entry in the database.

    Args:
        document_name (str): The name of the document.
        content (str): The content of the document that needs to be added to the storage.
        refresh (bool): If True, all existing entries for this document will be deleted before adding new ones.

    Returns:
        str: A message indicating the number of created chunks and their total text size.
    """
    preapare_state()
    settings: ServerSettings = service_state["settings"]
    engine = service_state["engine"]
    chunks = split_text(
        content, chunk_size=settings.chunk_size, tolerance=settings.tolerance / 100.0
    )
    index = volume = 0

    with Session(engine) as session:
        if refresh:
            # Delete all existing entries for this document
            query = sql_delete(DataStorageModel).where(DataStorageModel.document == document_name)
            session.execute(query)

        for chunk in chunks:
            index += 1
            model = DataStorageModel(document=document_name, chunk_index=index, text=chunk)
            session.add(model)
            volume += len(chunk)

        session.commit()

    return f"for document '{document_name}' created {index} chunks with text size: {volume}"


def add_document_to_storage(file_path: str) -> str:
    """
    Adds a document to the storage by reading its content, splitting it into chunks,
    and saving each chunk as an entry in the database.

    Args:
        file_path (str): The path to the document file that needs to be added to the storage.

    Returns:
        str: A message indicating the number of created chunks and their total text size.
    """
    file_name = os.path.basename(file_path)
    with open(file_path) as data_file:
        content = " ".join(line.strip() for line in data_file if line.strip())

    return add_document_content_to_storage(document_name=file_name, content=content, refresh=True)


def create_vectors(*documents: str, model_name: str = "") -> str:
    """
    Creates embeddings for each chunk of the specified documents.

    Args:
        *documents (str): Variable length argument list containing document names.
        model_name (str, optional): Name of the SentenceTransformer model to use. Defaults to settings.model_name if not provided.

    Returns:
        str: A message indicating the number of created vectors and the time taken for processing.
    """
    if not documents:
        return ""

    preapare_state()
    settings: ServerSettings = service_state["settings"]
    model = service_state.get("model")
    if model is None:
        model_name = model_name or settings.model_name
        model = SentenceTransformer(model_name)
        service_state["model"] = model

    engine = service_state["engine"]
    vec_dim = total = 0
    done_docs = []

    strat_time = monotonic()
    for document in set(documents):
        if not document:
            continue

        dt = now()
        with Session(engine) as session:
            query = select(DataStorageModel.id, DataStorageModel.text).where(
                DataStorageModel.document == document
            )
            rows = session.execute(query)
            for pk, text_data, *_ in rows:
                embedding = model.encode(text_data, **prompt_pr)
                vec_dim = len(embedding) or vec_dim
                if vec_dim > VEC_DIMENSIONS:
                    raise ValueError(
                        f"Vector dimension {vec_dim} exceeds the maximum allowed size of {VEC_DIMENSIONS}. "
                        "Please adjust your settings or use a different model."
                    )

                update_query = sql_update(DataStorageModel).where(
                    DataStorageModel.id == pk
                ).values(
                    vec=embedding, filled=dt
                ).execution_options(
                    synchronize_session="fetch"
                )
                session.execute(update_query)
                session.commit()
                total += 1

            done_docs.append(document)

    ms = int((monotonic() - strat_time) * 1000 + 1)
    doc_info = ", ".join(done_docs)
    return f"created {total} vectors (dimension {vec_dim}) per {ms} ms for documents: {doc_info}"


def select_chunks_for_request(
    request: str,
    l2_rate: float,
    cosine_rate: float,
    prompt_limit: int = 0,
    collect: bool = False,
    model_name: str = "",
) -> Dict[str, List[Dict[str, Union[str, float]]]]:
    """
    Selects chunks from the storage that match a given request based on L2 and cosine distance metrics.

    This function encodes the input request using a SentenceTransformer model,
    then queries the database for document chunks whose embeddings have an L2 or
    cosine distance within specified thresholds. The results are grouped by document name.

    Args:
        request (str): The text of the request to match against stored document chunks.
        l2_rate (float): The maximum allowed L2 distance between the request embedding and chunk embeddings.
        cosine_rate (float): The maximum allowed cosine distance between the request embedding and chunk embeddings.
        model_name (str, optional): Name of the SentenceTransformer model to use. Defaults to settings.model_name if not provided.
        prompt_limit (int, optional): Maximum number of tokens in the result. If set, the function will drop chunks with lower rates until the limit is met.
        collect (bool, optional): If True, collects all matched text data into a single string and returns it under the key 'data'.

    Returns:
        Dict[str, List[Dict[str, Union[str, float]]]]: A dictionary where keys are document names,
        and values are lists of dictionaries containing chunk text data, L2 distance, and cosine distance.
    """
    if not request:
        return ""

    result = defaultdict(list)
    preapare_state()
    settings: ServerSettings = service_state["settings"]
    model = service_state.get("model")
    engine = service_state["engine"]
    if model is None:
        model_name = model_name or settings.model_name
        model = SentenceTransformer(model_name)
        service_state["model"] = model

    chunks = split_text(
        request, chunk_size=settings.chunk_size, tolerance=settings.tolerance / 100.0
    )
    embeddings = [model.encode(chunk, **prompt_pr) for chunk in chunks]
    vec = DataStorageModel.vec
    l2_rate_value = func.least(*(vec.l2_distance(embedding) for embedding in embeddings))
    cosine_rate_value = func.least(*(vec.cosine_distance(embedding) for embedding in embeddings))
    with Session(engine) as session:
        s_query = select(
            DataStorageModel.document.label("doc"),
            l2_rate_value.label("l2_rate"),
            cosine_rate_value.label("cosine_rate"),
            DataStorageModel.text.label("txt")
        ).where(
            DataStorageModel.filled.is_not(None)
        ).order_by(
            DataStorageModel.document, DataStorageModel.chunk_index
        ).subquery()

        query = select(
            s_query.c.doc, s_query.c.txt, s_query.c.l2_rate, s_query.c.cosine_rate,
        ).where(
            (s_query.c.l2_rate <= l2_rate) | (s_query.c.cosine_rate <= cosine_rate)
        )
        for doc_name, text_data, l2, cos, *_ in session.execute(query):
            result[doc_name].append({"data": text_data, "l2": l2, "cosine": cos})

    if prompt_limit and result:
        current_size = result_token_count(result)
        while current_size > prompt_limit:
            drop_low_rate_chunk(result)
            current_size = result_token_count(result)

    if collect:
        text_result = []
        for doc_name, items in result.items():
            text_result.append(f"{settings.source_doc_label} {doc_name}")
            text_result.extend(item.get("data") for item in items)

        result = {"data": "\n".join(text_result)}

    return result
