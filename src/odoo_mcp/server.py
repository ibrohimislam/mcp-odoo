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

# @mcp.resource(
#     "odoo://models", description="List all available models in the Odoo system"
# )
# def get_models() -> str:
#     """Lists all available models in the Odoo system"""
#     odoo_client = get_odoo_client()
#     models = odoo_client.get_models()
#     return json.dumps(models, indent=2)


# @mcp.resource(
#     "odoo://model/{model_name}",
#     description="Get detailed information about a specific model including fields",
# )
# def get_model_info(model_name: str) -> str:
#     """
#     Get information about a specific model

#     Parameters:
#         model_name: Name of the Odoo model (e.g., 'res.partner')
#     """
#     odoo_client = get_odoo_client()
#     try:
#         # Get model info
#         model_info = odoo_client.get_model_info(model_name)

#         # Get field definitions
#         fields = odoo_client.get_model_fields(model_name)
#         model_info["fields"] = fields

#         return json.dumps(model_info, indent=2)
#     except Exception as e:
#         return json.dumps({"error": str(e)}, indent=2)


# @mcp.resource(
#     "odoo://record/{model_name}/{record_id}",
#     description="Get detailed information of a specific record by ID",
# )
# def get_record(model_name: str, record_id: str) -> str:
#     """
#     Get a specific record by ID

#     Parameters:
#         model_name: Name of the Odoo model (e.g., 'res.partner')
#         record_id: ID of the record
#     """
#     odoo_client = get_odoo_client()
#     try:
#         record_id_int = int(record_id)
#         record = odoo_client.read_records(model_name, [record_id_int])
#         if not record:
#             return json.dumps(
#                 {"error": f"Record not found: {model_name} ID {record_id}"}, indent=2
#             )
#         return json.dumps(record[0], indent=2)
#     except Exception as e:
#         return json.dumps({"error": str(e)}, indent=2)


# @mcp.resource(
#     "odoo://search/{model_name}/{domain}",
#     description="Search for records matching the domain",
# )
# def search_records_resource(model_name: str, domain: str) -> str:
#     """
#     Search for records that match a domain

#     Parameters:
#         model_name: Name of the Odoo model (e.g., 'res.partner')
#         domain: Search domain in JSON format (e.g., '[["name", "ilike", "test"]]')
#     """
#     odoo_client = get_odoo_client()
#     try:
#         results = odoo_client.search_read(model_name, domain)
#         return json.dumps(results, indent=2)
#     except Exception as e:
#         return json.dumps({"error": str(e)}, indent=2)


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
def get_record(
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
def search_record(
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

# @mcp.tool(description="Execute a custom method on an Odoo model")
# def execute_method(
#     ctx: Context,
#     model: str,
#     method: str,
#     args: List[Any] = None,
#     kwargs: Optional[Dict[str, Any]] = None,
# ) -> Dict[str, Any]:
#     """
#     Execute a custom method on an Odoo model

#     Parameters:
#         model: The model name (e.g., 'res.partner')
#         method: Method name to execute
#         args: Positional arguments
#         kwargs: Keyword arguments

#     Returns:
#         Dictionary containing:
#         - success: Boolean indicating success
#         - result: Result of the method (if success)
#         - error: Error message (if failure)
#     """
#     odoo = ctx.request_context.lifespan_context.odoo
#     try:
#         args = args or []
#         kwargs = kwargs or {}

#         # Special handling for search methods like search, search_count, search_read
#         search_methods = ["search", "search_count", "search_read"]
#         if method in search_methods and args:
#             # Search methods usually have domain as the first parameter
#             # args: [[domain], limit, offset, ...] or [domain, limit, offset, ...]
#             normalized_args = list(
#                 args
#             )  # Create a copy to avoid affecting the original args

#             if len(normalized_args) > 0:
#                 # Process domain in args[0]
#                 domain = normalized_args[0]
#                 domain_list = []

#                 # Check if domain is wrapped unnecessarily ([domain] instead of domain)
#                 if (
#                     isinstance(domain, list)
#                     and len(domain) == 1
#                     and isinstance(domain[0], list)
#                 ):
#                     # Case [[domain]] - unwrap to [domain]
#                     domain = domain[0]

#                 # Normalize domain similar to search_records function
#                 if domain is None:
#                     domain_list = []
#                 elif isinstance(domain, dict):
#                     if "conditions" in domain:
#                         # Object format
#                         conditions = domain.get("conditions", [])
#                         domain_list = []
#                         for cond in conditions:
#                             if isinstance(cond, dict) and all(
#                                 k in cond for k in ["field", "operator", "value"]
#                             ):
#                                 domain_list.append(
#                                     [cond["field"], cond["operator"], cond["value"]]
#                                 )
#                 elif isinstance(domain, list):
#                     # List format
#                     if not domain:
#                         domain_list = []
#                     elif all(isinstance(item, list) for item in domain) or any(
#                         item in ["&", "|", "!"] for item in domain
#                     ):
#                         domain_list = domain
#                     elif len(domain) >= 3 and isinstance(domain[0], str):
#                         # Case [field, operator, value] (not [[field, operator, value]])
#                         domain_list = [domain]
#                 elif isinstance(domain, str):
#                     # String format (JSON)
#                     try:
#                         parsed_domain = json.loads(domain)
#                         if (
#                             isinstance(parsed_domain, dict)
#                             and "conditions" in parsed_domain
#                         ):
#                             conditions = parsed_domain.get("conditions", [])
#                             domain_list = []
#                             for cond in conditions:
#                                 if isinstance(cond, dict) and all(
#                                     k in cond for k in ["field", "operator", "value"]
#                                 ):
#                                     domain_list.append(
#                                         [cond["field"], cond["operator"], cond["value"]]
#                                     )
#                         elif isinstance(parsed_domain, list):
#                             domain_list = parsed_domain
#                     except json.JSONDecodeError:
#                         try:
#                             import ast

#                             parsed_domain = ast.literal_eval(domain)
#                             if isinstance(parsed_domain, list):
#                                 domain_list = parsed_domain
#                         except:
#                             domain_list = []

#                 # Xác thực domain_list
#                 if domain_list:
#                     valid_conditions = []
#                     for cond in domain_list:
#                         if isinstance(cond, str) and cond in ["&", "|", "!"]:
#                             valid_conditions.append(cond)
#                             continue

#                         if (
#                             isinstance(cond, list)
#                             and len(cond) == 3
#                             and isinstance(cond[0], str)
#                             and isinstance(cond[1], str)
#                         ):
#                             valid_conditions.append(cond)

#                     domain_list = valid_conditions

#                 # Cập nhật args với domain đã chuẩn hóa
#                 normalized_args[0] = domain_list
#                 args = normalized_args

#                 # Log for debugging
#                 print(f"Executing {method} with normalized domain: {domain_list}")

#         result = odoo.execute_method(model, method, *args, **kwargs)
#         return {"success": True, "result": result}
#     except Exception as e:
#         return {"success": False, "error": str(e)}