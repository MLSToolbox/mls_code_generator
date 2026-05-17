"""ServicesFactory: Singleton factory to resolve service adapters."""

class ServicesFactory:
    """Singleton factory for service adapters."""

    _instance = None

    def __init__(self):
        self._adapters = {}

    @classmethod
    def get_instance(cls):
        """
        Return the singleton ServicesFactory instance.

        Returns:
            ServicesFactory
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def get_service_adapter(self, adapter_type: str = "flask"):
        """
        Return an adapter instance for the requested adapter_type.

        Args:
            adapter_type (str): adapter identifier, e.g. "flask".

        Returns:
            IServiceAdapter: concrete adapter instance.

        Raises:
            ValueError: if adapter_type is unknown.
        """
        adapter_type = (adapter_type or "flask").lower()
        if adapter_type in self._adapters:
            return self._adapters[adapter_type]

        if adapter_type == "flask":
            from mls_code_generator.adapters.flask_adapter import FlaskServiceAdapter
            adapter = FlaskServiceAdapter()
            self._adapters[adapter_type] = adapter
            return adapter

        raise ValueError(f"Unknown adapter_type: {adapter_type}")