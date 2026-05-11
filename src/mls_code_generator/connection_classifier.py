""" Connection classifier: component that analyses step-to-step connections"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any

from mls_code_generator.types.pipeline import Pipeline

class ConnectionType(Enum):
    """
    Simple enum for connection classification.
    """
    INTERNAL = "internal"
    EXTERNAL = "external"


@dataclass
class ConnectionInfo:
    """
    Holds metadata for a connection between two Steps.

    Attributes:
        source_step_id (str): Identifier of the source Step.
        source_service_id (str): Identifier of the Service that contains the source Step.
        source_port (str): Logical port name at the source (e.g. 'out', 'predictions').
        target_step_id (str): Identifier of the target Step.
        target_service_id (str): Identifier of the Service that contains the target Step.
        target_port (str): Logical port name at the target (e.g. 'in', 'dataframe').
        conn_type (ConnectionType): INTERNAL or EXTERNAL classification for this connection.
        raw (Any): Original low-level structure (optional). Kept for debugging or future use.
    """
    source_step_id: str
    source_service_id: str
    source_port: str
    target_step_id: str
    target_service_id: str
    target_port: str
    conn_type: ConnectionType
    raw: Any = None


def _step_id_of(obj) -> str:
    """
    Return the step id from a Step-like object or from a string id.

    Parameters:
        obj: Step instance (has attribute 'id') or string representing a step id.

    Returns:
        str: the resolved step id.
    """
    if hasattr(obj, "id"):
        return getattr(obj, "id")
    return str(obj)


def classify_pipeline_connections(pipeline: Pipeline) -> List[ConnectionInfo]:
    """
    Classify main connections between Steps as INTERNAL or EXTERNAL.

    Parameters:
        pipeline (Pipeline): pipeline populated by PipelineLoader.

    Returns:
        List[ConnectionInfo]: list of classified connections.
    """
    step_to_service: Dict[str, str] = {}
    for svc_id, svc in pipeline.services.items():
        for s in getattr(svc, "steps", []):
            sid = _step_id_of(s)
            step_to_service[sid] = svc_id

    for step_id in pipeline.steps.keys():
        if step_id not in step_to_service:
            step_to_service[step_id] = "monolith"

    connections: List[ConnectionInfo] = []

    for target_step in pipeline.steps.values():
        target_id = _step_id_of(target_step)
        target_service = step_to_service.get(target_id, "monolith")

        for dep in getattr(target_step, "dependencies", []):
            if len(dep) < 3:
                continue

            source_obj, source_port, target_port = dep[0], dep[1], dep[2]
            source_id = _step_id_of(source_obj)
            source_service = step_to_service.get(source_id, "monolith")

            conn_type = (
                ConnectionType.INTERNAL
                if source_service == target_service
                else ConnectionType.EXTERNAL
            )

            ci = ConnectionInfo(
                source_step_id=source_id,
                source_service_id=source_service,
                source_port=source_port,
                target_step_id=target_id,
                target_service_id=target_service,
                target_port=target_port,
                conn_type=conn_type,
                raw=dep,
            )
            connections.append(ci)

            if conn_type is ConnectionType.EXTERNAL:
                if not hasattr(pipeline.steps[source_id], "external_outgoing"):
                    setattr(pipeline.steps[source_id], "external_outgoing", [])
                pipeline.steps[source_id].external_outgoing.append(ci)

                if not hasattr(pipeline.steps[target_id], "external_incoming"):
                    setattr(pipeline.steps[target_id], "external_incoming", [])
                pipeline.steps[target_id].external_incoming.append(ci)

    return connections