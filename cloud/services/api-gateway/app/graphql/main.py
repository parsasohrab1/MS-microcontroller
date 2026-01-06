"""
GraphQL API Endpoint
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.graphql import GraphQLApp
from graphene import Schema
import json

from .schema import schema

app = FastAPI(title="GraphQL API")

# GraphQL endpoint
app.add_route("/graphql", GraphQLApp(schema=schema))

# GraphQL Playground (برای development)
@app.get("/graphql/playground")
async def graphql_playground():
    """GraphQL Playground UI"""
    # TODO: بازگشت HTML برای GraphQL Playground
    return {"message": "GraphQL Playground"}


# Health check
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "GraphQL API"}

