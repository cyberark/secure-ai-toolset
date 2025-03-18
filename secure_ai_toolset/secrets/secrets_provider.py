# this is a abstract class for secrets provider
import abc
import logging


class BaseSecretsProvider(abc.ABC):

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)

    @abc.abstractmethod
    def connect(self) -> str:
        pass

    @abc.abstractmethod
    def store(self, key: str, secret: str) -> None:
        pass

    @abc.abstractmethod
    def get(self, key: str) -> str:
        pass

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        pass
