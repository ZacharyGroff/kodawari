from os import getenv
from typing import Any

from acsylla import (
    Cluster,
    PreparedStatement,
    Result,
    Row,
    Session,
    Statement,
    create_cluster,
)

_cassandra_cluster_name_environment_variable: str = "CASSANDRA_CLUSTER_NAME"
_connection_timeout_seconds: int = 30
_request_timeout_seconds: int = 30
_resolve_timeout_seconds: int = 10


async def get_cassandra_session(keyspace_name: str) -> Session:
    """Retrieves an acsylla Session object, for accessing Cassandra.

    Retrieves an acsylla Session object after connecting to a cassandra cluster specified by the environment variable CASSANDRA_CLUSTER_NAME.

    Args:
        keyspace_name: The name of the keyspace to create a session for.
    Returns:
        An acsylla.Session object, for accessing Cassandra.
    Raises:
        Exception: CASSANDRA_CLUSTER_NAME is not set.
    """
    cassandra_cluster_name: str | None = getenv(
        _cassandra_cluster_name_environment_variable
    )
    if cassandra_cluster_name is None:
        raise Exception(f"{_cassandra_cluster_name_environment_variable} is not set")

    cluster: Cluster = create_cluster(
        [cassandra_cluster_name],
        connect_timeout=_connection_timeout_seconds,
        request_timeout=_request_timeout_seconds,
        resolve_timeout=_resolve_timeout_seconds,
    )
    session = await cluster.create_session(keyspace=keyspace_name)

    return session


async def get_resource_by_id(
    session: Session, table_name: str, id: int
) -> dict[str, Any] | None:
    """Retrieves a resource from cassandra by it's identifier.

    Args:
        session: An acsylla.Session object.
        table_name: The name of the cassandra table to query.
        id: The identifier for the resource to get.

    Returns:
        A dictionary containing the contents of the table row for the requested resource, or None if no resource is found.
    Raises:
        Exception: Multiple results returned when querying for resource.
    """
    prepared: PreparedStatement = await session.create_prepared(
        f"SELECT * FROM {table_name} WHERE id=?"
    )
    statement: Statement = prepared.bind()
    statement.bind(0, id)
    result: Result = await session.execute(statement)

    if result.count() > 1:
        raise Exception(
            f"Multiple results returned when querying {table_name} with id: {id}"
        )

    table_row: Row | None = result.first()
    return table_row.as_dict() if table_row is not None else None


async def create_resource(
    session: Session, table_name: str, column_names: list[str], values: list[Any]
) -> None:
    """Creates a resource in cassandra.

    Args:
        session: An acsylla.Session object.
        table_name: The name of the cassandra table create a resource in.
        column_names: A list of the names of columns for the cassandra table.
        values: A list of values to insert into the given columns.
    """
    prepared: PreparedStatement = await session.create_prepared(
        f"INSERT INTO {table_name} ({', '.join(column_names)}) VALUES ({', '.join(['?' for _ in range(len(values))])})"
    )
    statement: Statement = prepared.bind()
    statement.bind_list(values)
    await session.execute(statement)


async def patch_resource(
    session: Session, table_name: str, to_patch: dict[str, Any], id: int
) -> None:
    """Patches a resource, identified with the specified id, in cassandra.

    Args:
        session: An acsylla.Session object.
        table_name: The name of the table to run the patch statement.
        to_patch: A dictionary key-value pairs to include in the UPDATE statement.
        id: The id of the resource being patched.
    """
    eligible_fields: list[str] = []
    eligible_values: list[Any] = []
    for key, value in to_patch.items():
        if value is not None and key != "id":
            eligible_fields.append(key)
            eligible_values.append(value)

    if len(eligible_fields) < 1:
        return None

    fields: str = "=?, ".join(eligible_fields) + "=?"
    prepared: PreparedStatement = await session.create_prepared(
        f"UPDATE {table_name} SET {fields} WHERE id=? IF EXISTS",
    )
    statement: Statement = prepared.bind()
    statement.bind_list(eligible_values + [id])
    await session.execute(statement)


async def delete_resource_by_id(session: Session, table_name: str, id: int) -> None:
    """Deletes a resource from cassandra by it's identifier.

    Args:
        session: An acsylla.Session object.
        table_name: The name of the cassandra table to query.
        id: The identifier for the resource to delete.
    """

    prepared: PreparedStatement = await session.create_prepared(
        f"DELETE FROM {table_name} WHERE id=? IF EXISTS"
    )
    statement: Statement = prepared.bind()
    statement.bind(0, id)
    await session.execute(statement)
