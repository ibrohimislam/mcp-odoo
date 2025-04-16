"""
MCP server for Odoo integration

Provides MCP tools and resources for interacting with Odoo ERP systems
"""

import logging
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, AsyncIterator, Dict, List, Optional, Union, cast, TypeVar, Generic

from mcp.server import Context, FastMCP
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


# Define a detailed prompt for the MCP tool
ODOO_PROMPT = """
# Odoo MCP Agent

This agent helps you interact with Odoo ERP systems through a set of specialized tools.

## Common Odoo Models
- `res.partner` - Contacts (customers, suppliers, etc.)
- `sale.order` - Sales orders/quotations
- `purchase.order` - Purchase orders
- `account.move` - Invoices, bills, and accounting entries
- `product.template` - Product information
- `product.product` - Product variants
- `stock.move` - Inventory movements
- `project.task` - Project tasks

## Working with Odoo Domains
Odoo uses domain expressions for filtering records. Domains are lists of criteria:

```
[
  ["field_name", "operator", value],
  ["another_field", "operator", value]
]
```

### Common Operators
- `=`, `!=`: Equality/inequality
- `>`, `>=`, `<`, `<=`: Comparison
- `like`, `ilike`: Pattern matching (% is wildcard)
- `in`, `not in`: Value in list
- `child_of`: Hierarchical search
- `&`, `|`, `!`: Logical operators (default is &)

### Domain Examples
- Active companies: `[["is_company", "=", true], ["active", "=", true]]`
- Recent sales: `[["create_date", ">", "2023-01-01"]]`
- Specific status: `[["state", "in", ["draft", "sent"]]]`
- Name search: `[["name", "ilike", "%search term%"]]`

## Important Fields by Model
- res.partner: name, email, phone, is_company, country_id
- sale.order: name, partner_id, date_order, amount_total, state
- product.template: name, list_price, default_code, categ_id, type
- account.move: name, partner_id, invoice_date, amount_total, state

## Tips for Effective Queries
1. Always limit your result set when possible
2. Use proper field types (dates as strings, IDs as integers)
3. For relational fields, use the ID (integer) in domains
4. For complex data analysis, use read_group for server-side aggregation
5. Retrieve only the fields you need by specifying the fields parameter

## Common Workflows
- Get model data: Use model_info to explore fields
- Find records: Use search_read with appropriate domains
- Count records: Use search_count for quick counts
- Analyze data: Use read_group for aggregations
"""

# Create MCP server
mcp = FastMCP(
    name="Odoo MCP Server", 
    description="MCP Server for interacting with Odoo ERP systems",
    dependencies=["requests"],
    lifespan=app_lifespan,
    prompt=ODOO_PROMPT,
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
def list_models(ctx: Context) -> Dict[str, Any]:
    """
    Retrieves all available models in the Odoo system.
    
    Returns a dictionary mapping model technical names to their display names.
    Common models include: res.partner, sale.order, account.move, product.template
    
    Example response:
    {
        "res.partner": {"name": "Contact"},
        "sale.order": {"name": "Sales Order"}
    }
    """
    try:
        odoo_client = get_odoo_client()
        models = odoo_client.get_models()
        _logger.info(models)
        return {"success": True, "result": models}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(description="Get detailed information about a specific Odoo model including its fields definitions")
def model_info(
    ctx: Context,
    model_name: str,
) -> Dict[str, Any]:
    """
    Retrieves detailed information about an Odoo model including its fields definitions.

    Parameters:
        model_name: Technical name of the Odoo model (e.g., 'res.partner', 'sale.order')
    
    Returns information about:
    - Model name and description
    - All available fields with their types, labels, help text, and constraints
    - Field attributes (readonly, required, selection values, related fields, etc)
    
    Common field types in Odoo:
    - char: Text field (limited length)
    - text: Multiline text field
    - integer: Integer field
    - float: Decimal number field
    - boolean: True/False field
    - date: Date field
    - datetime: Date and time field
    - many2one: Relation to a single record of another model
    - one2many: Relation to multiple records where this model is referenced
    - many2many: Relation to multiple records with a join table
    - selection: Field with predefined selection options
    - binary: Binary data field (for files/images)
    
    
    Examples:
        - Contact model: model_name="res.partner"
        - Sales model: model_name="sale.order"
        - Product model: model_name="product.template"
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

@mcp.tool(description="Get detailed information of a specific record by ID from an Odoo model")
def read(
    ctx: Context,
    model_name: str,
    record_id: Union[str, int],
    fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Retrieves a specific record by ID from an Odoo model.

    Parameters:
        model_name: Technical name of the Odoo model (e.g., 'res.partner', 'sale.order')
        record_id: Database ID of the record to retrieve
        fields: List of specific fields to retrieve. If None, all fields are retrieved.
               Common fields by model:
               - res.partner: name, email, phone, street, city, country_id, is_company
               - sale.order: name, partner_id, date_order, amount_total, state
               - product.template: name, list_price, default_code, categ_id
               
    Examples:
        - Get contact: model_name="res.partner", record_id=5
        - Get sale order with specific fields: model_name="sale.order", record_id=42, fields=["name", "amount_total", "state"]
    """
    try:
        odoo_client = get_odoo_client()
        record_id_int = int(record_id)
        record = odoo_client.read_records(model_name, [record_id_int], fields)
        _logger.info(record)
        if not record:
            return {"success": False, "error": f"Record {record_id_int} not found in model {model_name}."}
        return {"success": True, "result": record}
    except ValueError:
        return {"success": False, "error": f"Invalid record ID: {record_id}. Must be a valid integer."}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(description="Count records matching the domain criteria in an Odoo model")
def search_count(
    ctx: Context,
    model_name: str,
    domain: List[Union[str, List[Any]]] = [],
) -> Dict[str, Any]:
    """
    Counts records in an Odoo model that match specified criteria.

    Parameters:
        model_name: Technical name of the Odoo model (e.g., 'res.partner', 'sale.order')
        domain: Odoo domain filter expressed as a list of conditions. Each condition is a list with 3 elements:
               [field_name, operator, value]
               
               Common operators: =, !=, >, >=, <, <=, like, ilike, in, not in, child_of
               
    Examples:
        - Count all contacts: model_name="res.partner", domain=[]
        - Count companies: model_name="res.partner", domain=[["is_company", "=", true]]
        - Count draft sales: model_name="sale.order", domain=[["state", "=", "draft"]]
        - Count recent invoices: model_name="account.move", domain=[
            ["type", "=", "out_invoice"], 
            ["date", ">", "2023-01-01"]
          ]
    """
    try:
        odoo_client = get_odoo_client()
        results = odoo_client.search_count(model_name, domain)
        _logger.info(results)
        return {"success": True, "result": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(description="Search and read records from an Odoo model that match specified criteria")
def search_read(
    ctx: Context,
    model_name: str,
    domain: List[Union[str, List[Any]]] = [],
    fields: Optional[List[str]] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    order: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search and read records from an Odoo model that match specified criteria.

    Parameters:
        model_name: Technical name of the Odoo model (e.g., 'res.partner', 'sale.order')
        domain: Odoo domain filter expressed as a list of conditions. Each condition is a list with 3 elements:
               [field_name, operator, value]
               
               Common operators: =, !=, >, >=, <, <=, like, ilike, in, not in, child_of
        fields: List of field names to retrieve. If None, all fields are retrieved.
               Common fields by model:
               - res.partner: name, email, phone, street, city, country_id, is_company
               - sale.order: name, partner_id, date_order, amount_total, state
               - product.template: name, list_price, default_code, categ_id
        limit: Maximum number of records to return (default: all records)
        offset: Number of records to skip (for pagination)
        order: Sort order specification (e.g., "name ASC", "create_date DESC")
               
    Examples:
        - All contacts: model_name="res.partner"
        - Companies only: model_name="res.partner", domain=[["is_company", "=", true]]
        - Recent sales: model_name="sale.order", domain=[["create_date", ">", "2023-01-01"]]
        - Products by category: model_name="product.template", domain=[["categ_id", "=", 4]]
    """
    try:
        odoo_client = get_odoo_client()
        kwargs = {}
        if fields is not None:
            kwargs['fields'] = fields
        if limit is not None:
            kwargs['limit'] = limit
        if offset is not None:
            kwargs['offset'] = offset
        if order is not None:
            kwargs['order'] = order
        results = odoo_client.execute_method(model_name, 'search_read', domain, **kwargs)
        _logger.info(results)
        return {"success": True, "result": results}
    except Exception as e:
        return {"success": False, "error": str(e)}

@mcp.tool(description="Group and aggregate data from Odoo models with optional aggregation functions")
def read_group(
    ctx: Context,
    model_name: str,
    domain: List[Union[str, List[Any]]] = [],
    fields: List[str] = [],
    groupby: List[str] = [],
    lazy: Optional[bool] = True,
) -> Dict[str, Any]:
    """
    Groups and aggregates records from an Odoo model, similar to SQL GROUP BY with aggregate functions.

    Parameters:
        model_name: Technical name of the Odoo model (e.g., 'sale.order', 'account.move')
        domain: Odoo domain filter expressed as a list of conditions. Each condition is a list with 3 elements:
               [field_name, operator, value]
        fields: Fields to include or aggregate, optionally using functions like count, sum, avg, min, max.
               Format: ['field_name', 'field_name:function']
               Examples:
               - 'amount_total:sum' - sum of amount_total field
               - 'line_ids:count' - count of related lines
               - 'price:avg' - average price
        groupby: List of fields to group by. These can be date fields with special intervals.
               Examples:
               - ['partner_id'] - group by partner
               - ['date:month'] - group by month
               - ['product_id', 'categ_id'] - group by product and category
               - [] - no grouping, just aggregation of all matching records
        lazy: If True, only the first groupby level is computed (better performance)
               
    Examples:
        - Sales by customer: model_name="sale.order", fields=["amount_total:sum"], groupby=["partner_id"]
        - Invoice totals by month: model_name="account.move", fields=["amount_total:sum"], groupby=["date:month"]
        - Product sales by category: model_name="product.template", fields=["qty_sold:sum"], groupby=["categ_id"]
        - Total sales: model_name="sale.order", fields=["amount_total:sum"], groupby=[]
    """
    if not fields:
        return {"success": False, "error": "The 'fields' parameter must not be empty"}
    
    try:
        odoo_client = get_odoo_client()
        kwargs = {}
        kwargs['fields'] = fields
        kwargs['groupby'] = groupby
        kwargs['lazy'] = lazy
        
        results = odoo_client.execute_method(model_name, 'read_group', domain, **kwargs)
        _logger.info(results)
        return {"success": True, "result": results}
    except Exception as e:
        return {"success": False, "error": str(e)}