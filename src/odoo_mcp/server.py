"""
MCP server for Odoo integration

Provides MCP tools and resources for interacting with Odoo ERP systems
"""

import logging
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional, Union, cast

from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

from .odoo_client import OdooClient, get_odoo_client

_logger = logging.getLogger(__name__)

@dataclass
class AppContext:
    """Application context for the MCP server"""

    odoo: OdooClient


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Application lifespan for initialization and cleanup
    """
    # Initialize Odoo client on startup
    odoo_client = get_odoo_client()

    try:
        yield AppContext(odoo=odoo_client)
    finally:
        # No cleanup needed for Odoo client
        pass


# Create MCP server
mcp = FastMCP(
    "Odoo MCP Server",
    description="MCP Server for interacting with Odoo ERP systems",
    dependencies=["requests"],
    lifespan=app_lifespan,
)


# ----- MCP Resources -----

@mcp.resource(
    "odoo://models", description="List all available models in the Odoo system"
)
def get_models() -> str:
    """Lists all available models in the Odoo system"""
    odoo_client = get_odoo_client()
    models = odoo_client.get_models()
    return json.dumps(models, indent=2)


@mcp.resource(
    "odoo://model/{model_name}",
    description="Get detailed information about a specific model including fields",
)
def get_model_info(model_name: str) -> str:
    """
    Get information about a specific model

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
    """
    odoo_client = get_odoo_client()
    try:
        # Get model info
        model_info = odoo_client.get_model_info(model_name)

        # Get field definitions
        fields = odoo_client.get_model_fields(model_name)
        model_info["fields"] = fields

        return json.dumps(model_info, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://record/{model_name}/{record_id}",
    description="Get detailed information of a specific record by ID",
)
def get_record(model_name: str, record_id: str) -> str:
    """
    Get a specific record by ID

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
        record_id: ID of the record
    """
    odoo_client = get_odoo_client()
    try:
        record_id_int = int(record_id)
        record = odoo_client.read_records(model_name, [record_id_int])
        if not record:
            return json.dumps(
                {"error": f"Record not found: {model_name} ID {record_id}"}, indent=2
            )
        return json.dumps(record[0], indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


@mcp.resource(
    "odoo://search/{model_name}/{domain}",
    description="Search for records matching the domain",
)
def search_records_resource(model_name: str, domain: str) -> str:
    """
    Search for records that match a domain

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
        domain: Search domain in JSON format (e.g., '[["name", "ilike", "test"]]')
    """
    odoo_client = get_odoo_client()
    try:
        results = odoo_client.search_read(model_name, domain)
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)}, indent=2)


# ----- MCP Tools -----

@mcp.tool(description="List all available models in the Odoo system")
def list_models(ctx: Context,) -> Dict[str, Any]:
    """Lists all available models in the Odoo system"""
    try:
        odoo_client = get_odoo_client()
        models = odoo_client.get_models()
        _logger.info(models)
        return {"success": True, "result": models}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(description="Get detailed information about a specific model including fields")
def model_info(
    ctx: Context,
    model_name: str,
) -> Dict[str, Any]:
    """
    Get information about a specific model

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
    """
    try:
        odoo_client = get_odoo_client()
        model_info = odoo_client.get_model_info(model_name)
        fields = odoo_client.get_model_fields(model_name)
        model_info["fields"] = fields
        _logger.info(model_info)
        return {"success": True, "result": model_info}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(description="Get detailed information of a specific record by ID")
def read(
    ctx: Context,
    model_name: str,
    record_id: str,
) -> Dict[str, Any]:
    """
    Get a specific record by ID

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
        record_id: ID of the record
    """
    try:
        odoo_client = get_odoo_client()
        record_id_int = int(record_id)
        record = odoo_client.read_records(model_name, [record_id_int])
        _logger.info(record)
        if not record:
            return {"success": False, "error": f"Record {record_id_int} not found."}
        return {"success": True, "result": record}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(description="Count records matching the domain")
def search_count(
    ctx: Context,
    model_name: str,
    domain: List[str|List[str]] = [],
) -> int:
    """
    Search for records that match a domain

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
        domain: Search domain
    """
    try:
        odoo_client = get_odoo_client()
        results = odoo_client.search_count(model_name, domain)
        _logger.info(results)
        return {"success": True, "result": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(description="Search for records matching the domain")
def search_read(
    ctx: Context,
    model_name: str,
    domain: List[str|List[str]] = [],
    fields: Optional[List[str]] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Search for records that match a domain

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
        domain: Search domain
        fields: Select field
    """
    try:
        odoo_client = get_odoo_client()
        kwargs = {}
        if fields != None:
            kwargs['fields'] = fields
        if limit != None:
            kwargs['limit'] = limit
        results = odoo_client.execute_method(model_name, 'search_read', domain, **kwargs)
        _logger.info(results)
        return {"success": True, "result": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(description="Aggregates and groups model records by one or more fields. Returns a list of grouped dictionaries with aggregated data. Fields to include or aggregate, optionally using functions like count, sum, avg, min, max (e.g., 'amount_total:sum', 'state')")
def read_group(
    ctx: Context,
    model_name: str,
    domain: List[str|List[str]] = [],
    fields: Optional[List[str]] = None,
    groupby: List[str] = [],
) -> Dict[str, Any]:
    """
    Aggregates and groups model records by one or more fields, optionally computing aggregates like counts, sums, or averages. Returns a list of grouped dictionaries with aggregated data.

    Parameters:
        model_name: Name of the Odoo model (e.g., 'res.partner')
        domain: List of filter conditions (e.g., [('state', '=', 'sale')])
        fields: Fields to include or aggregate, optionally using functions like count, sum, avg, min, max (e.g., 'amount_total:sum', 'state')
        groupby: List of fields to group by (e.g., ['state'])
    """
    if len(fields) == 0:
        return {"success": False, "error": "Argument fields must not empty"}
    
    try:
        odoo_client = get_odoo_client()
        kwargs = {}
        if fields != None:
            kwargs['fields'] = fields
        if groupby != None:
            kwargs['groupby'] = groupby
        results = odoo_client.execute_method(model_name, 'read_group', domain, **kwargs)
        _logger.info(results)
        return {"success": True, "result": results}
    except Exception as e:
        return {"success": False, "error": str(e)}