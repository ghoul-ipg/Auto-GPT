import pinecone
from colorama import Fore, Style

from autogpt.llm_utils import create_embedding_with_ada
from autogpt.memory.base import MemoryProviderSingleton
from environments import PINECONE_API_KEY, PINECONE_REGION
from utils import get_logger

logger = get_logger(__name__)


class PineconeMemory(MemoryProviderSingleton):
    def __init__(self):
        pinecone_api_key = PINECONE_API_KEY
        pinecone_region = PINECONE_REGION
        pinecone.init(api_key=pinecone_api_key, environment=pinecone_region)
        dimension = 1536
        metric = "cosine"
        pod_type = "p1"
        table_name = "auto-gpt"
        # this assumes we don't start with memory.
        # for now this works.
        # we'll need a more complicated and robust system if we want to start with
        #  memory.
        self.vec_num = 0

        try:
            pinecone.whoami()
        except Exception as e:
            logger.debug(f"FAILED TO CONNECT TO PINECONE: {Style.BRIGHT + str(e) + Style.RESET_ALL}")
            logger.error(
                "Please ensure you have setup and configured Pinecone properly for use."
                + f"You can check out {Fore.CYAN + Style.BRIGHT}"
                  "https://github.com/Torantulino/Auto-GPT#-pinecone-api-key-setup"
                  f"{Style.RESET_ALL} to ensure you've set up everything correctly."
            )
            exit(1)

        if table_name not in pinecone.list_indexes():
            pinecone.create_index(
                table_name, dimension=dimension, metric=metric, pod_type=pod_type
            )
        self.index = pinecone.Index(table_name)

    def add(self, data):
        vector = create_embedding_with_ada(data)
        # no metadata here. We may wish to change that long term.
        self.index.upsert([(str(self.vec_num), vector, {"raw_text": data})])
        _text = f"Inserting data into memory at index: {self.vec_num}:\n data: {data}"
        self.vec_num += 1
        return _text

    def get(self, data):
        return self.get_relevant(data, 1)

    def clear(self):
        self.index.delete(deleteAll=True)
        return "Obliviated"

    def get_relevant(self, data, num_relevant=5):
        """
        Returns all the data in the memory that is relevant to the given data.
        :param data: The data to compare to.
        :param num_relevant: The number of relevant data to return. Defaults to 5
        """
        query_embedding = create_embedding_with_ada(data)
        results = self.index.query(
            query_embedding, top_k=num_relevant, include_metadata=True
        )
        sorted_results = sorted(results.matches, key=lambda x: x.score)
        return [str(item["metadata"]["raw_text"]) for item in sorted_results]

    def get_stats(self):
        return self.index.describe_index_stats()
