"""IServiceAdapter: Interface for service adapters."""

from abc import ABC, abstractmethod


class IServiceAdapter(ABC):
    """Adapter interface for generating service artifacts."""

    @abstractmethod
    def generate_service_code(self, service, output_path: str) -> None:
        """
        Generate the server files for `service` into `output_path`.

        Args:
            service: Service domain object (has at least `service_id` and `steps`).
            output_path (str): Directory where adapter must write generated files.

        Returns:
            None
        """
        raise NotImplementedError