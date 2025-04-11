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
from mcp.server.stdio import stdio_server
from mcp.server.lowlevel import Server
import mcp.types as types

from odoo_mcp.server import mcp  # FastMCP instance from our code


def setup_logging():
    """Set up logging to both console and file"""
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    return logger


def main() -> int:
    """
    Run the MCP server based on the official examples
    """
    logger = setup_logging()
    
    try:
        logger.info("=== ODOO MCP SERVER STARTING ===")
        logger.info(f"Python version: {sys.version}")
        logger.info("Environment variables:")
        for key, value in os.environ.items():
            if key.startswith("ODOO_"):
                if key == "ODOO_PASSWORD":
                    logger.info(f"  {key}: ***hidden***")
                else:
                    logger.info(f"  {key}: {value}")
        
        logger.info(f"MCP object type: {type(mcp)}")
        
        # Run server in stdio mode like the official examples
        logger.info("Starting Odoo MCP server with sse transport...")
        app = Starlette(routes=[Mount('/', app=mcp.sse_app())])
        app.router.routes.append(Host('mcp.acme.corp', app=mcp.sse_app()))
                
        uvicorn.run(app, host='0.0.0.0', port=8000)
        logger.info("MCP server stopped normally")
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main()) 
