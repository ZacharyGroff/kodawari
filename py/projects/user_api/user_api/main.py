from logging import DEBUG, Logger
from typing import Any

from acsylla import (
    Cluster,
    Result,
    Session,
    Statement,
    create_cluster,
    create_statement,
)
from authentication.authentication import BearerClaims, authenticate
from fastapi import Depends, FastAPI, HTTPException, Response, status
from logging_utilities.utilities import get_logger
from models.user import UserCreateRequest, UserPatchRequest

logger: Logger = get_logger(__name__, DEBUG)
app = FastAPI()
cluster: Cluster = create_cluster(["cassandra"])

current_id = 0


def get_id() -> int:
    global current_id
    current_id += 1
    return current_id


@app.get("/health")
async def health():
    return "healthy"


@app.get("/user/{id}", status_code=status.HTTP_200_OK)
async def get(id: int):
    session: Session = await cluster.create_session(keyspace="kodawari")
    statement: Statement = create_statement(
        "SELECT * FROM user WHERE id=?", parameters=1
    )
    statement.bind(0, id)
    result: Result = await session.execute(statement)

    if result.count() == 0:
        raise HTTPException(status_code=404, detail="User not found")
    elif result.count() > 1:
        logger.error(f"Multiple results returned when querying for user with id: {id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return result.first()


@app.post("/user", status_code=status.HTTP_201_CREATED)
async def post(response: Response, user_create_request: UserCreateRequest):
    session: Session = await cluster.create_session(keyspace="kodawari")
    statement: Statement = create_statement(
        "INSERT INTO user (id, display_name, description, joined) VALUES (?, ?, ?, toTimestamp(now()))",
        parameters=3,
    )

    user_id: int = get_id()
    arguments: list[Any] = [
        user_id,
        user_create_request.display_name,
        user_create_request.description,
    ]
    statement.bind_list(arguments)

    await session.execute(statement)

    response.headers["Location"] = f"/user/{user_id}"
    response.headers["Cache-Control"] = "no-cache"

    return {"message": "created"}


@app.patch("/user", status_code=status.HTTP_204_NO_CONTENT)
async def patch(
    user_patch_request: UserPatchRequest,
    bearer_claims: BearerClaims = Depends(authenticate),
):
    session: Session = await cluster.create_session(keyspace="kodawari")
    statement: Statement = create_statement(
        "UPDATE user SET display_name=?, description=? WHERE id=? IF EXISTS",
        parameters=3,
    )

    arguments: list[Any] = [
        user_patch_request.display_name,
        user_patch_request.description,
        bearer_claims.id,
    ]
    statement.bind_list(arguments)

    await session.execute(statement)

    return {"message": "patched"}


@app.delete("/user", status_code=status.HTTP_204_NO_CONTENT)
async def delete(bearer_claims: BearerClaims = Depends(authenticate)):
    session: Session = await cluster.create_session(keyspace="kodawari")
    statement: Statement = create_statement(
        "DELETE FROM user WHERE id=? IF EXISTS", parameters=1
    )
    statement.bind(0, bearer_claims.id)
    await session.execute(statement)
