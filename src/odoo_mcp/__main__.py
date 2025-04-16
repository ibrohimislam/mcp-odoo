"""
Command line entry point for the Odoo MCP Server
"""
import sys
import os
import logging
import uvicorn
from importlib import import_module
from starlette.applications import Starlette
from starlette.routing import Host, Mount

from .server import mcp

_logger = logging.getLogger(__name__)

def main() -> int:
    """
    Run the MCP server
    """
    try:
        # Print startup information
        _logger.info("=== ODOO MCP SERVER STARTING ===")
        _logger.info(f"Python version: {sys.version}")
        _logger.info("Environment variables:")
        for key, value in os.environ.items():
            if key.startswith("ODOO_"):
                if key == "ODOO_PASSWORD":
                    _logger.info(f"  {key}: ***hidden***")
                else:
                    _logger.info(f"  {key}: {value}")
        
        _logger.info(f"MCP object type: {type(mcp)}")
        
        # Run server in HTTP mode
        _logger.info("Starting Odoo MCP server with HTTP transport...")
        
        # Create a Starlette app and mount the FastMCP SSE app
        app = Starlette(
            routes=[
                Mount('/', app=mcp.sse_app()),
                Host('mcp.acme.corp', app=mcp.sse_app())
            ]
        )
        
        uvicorn.run(app, host='0.0.0.0', port=8000)
        _logger.info("MCP server stopped normally")
        return 0
    except Exception as e:
        _logger.error(f"Error starting server: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
