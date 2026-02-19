import json
import os
from abc import ABC, abstractmethod

from aiofile import async_open

from .wrapper import WrapperBase

__all__ = (
    "ManagerBase",
)


class ManagerBase(ABC):
    def __init__(self, _dir: str, name: str):
        self.__dir = _dir
        self.file_path = f"{self.__dir}/{name}.json"

    @abstractmethod
    async def load(self, *, name: str):
        """Initialiser, will create necessary directories. Must be overridden

        Args:
            name (str): The name of the manager
        """
        if not os.path.exists(self.__dir):
            os.mkdir(self.__dir)

        await self._get_or_create_wrapper()
        print(f"[{name}] Successfully loaded")

    async def __get_wrapper_data(self) -> dict:
        """Get wrapper data from disk

        Raises:
            FileNotFoundError: Wrapper data file was not found on disk

        Returns:
            dict: Wrapper data dict
        """
        async with async_open(self.file_path, "r") as afile:
            return json.loads(await afile.read())

    async def write(self, wrapper: WrapperBase) -> None:
        """Writes wrapper data to disk

        Args:
            wrapper (WrapperBase): The wrapper object to serialise
        """
        async with async_open(self.file_path, "w") as afile:
            await afile.write(json.dumps(wrapper.serialise(), indent=4))

    @abstractmethod
    async def _get_or_create_wrapper(self, *, cls: WrapperBase.__class__) -> WrapperBase:
        """Get wrapper from data, or create datafile if it doesn't exist. Must be overridden

        Args:
            cls (WrapperBase.__class__): Class that inherits from WrapperBase

        Returns:
            WrapperBase: An instantiated wrapper
        """
        try:
            data = await self.__get_wrapper_data()
        except FileNotFoundError:
            data = {}
            async with async_open(self.file_path, "w") as afile:
                await afile.write(data)
        return cls.parse(data)
