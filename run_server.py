#!/usr/bin/env python
"""
Standalone script to run the Odoo MCP server 
Uses the same approach as in the official MCP SDK examples
"""
import sys
import os
import asyncio
import uvicorn
import logging
import datetime

from starlette.applications import Starlette
from starlette.routing import Mount, Host
import mcp.types as types

from odoo_mcp.server import mcp  # FastMCP instance from our code


_logger = logging.getLogger(__name__)


def main() -> int:
    """
    Run the MCP server based on the official examples
    """
    
    try:
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
        app = mcp.get_app()
        # Add host route for development
        app.router.routes.append(Host('mcp.acme.corp', app=app))
                
        uvicorn.run(app, host='0.0.0.0', port=8000)
        _logger.info("MCP server stopped normally")
        return 0
        
    except Exception as e:
        _logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 
