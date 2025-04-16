# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Changed
- Upgraded MCP dependency from 0.1.1 to 1.6.0
- Updated server implementation to use the new MCP 1.6.0 API
- Fixed imports to match MCP 1.6.0 package structure (Context → RequestContext)
- Changed FastMCP initialization to use named parameters
- Enhanced type hints using precise typing (List, Union, etc.)
- Reimplemented __main__.py to directly use the MCP API for serving HTTP requests
- Added proper logging to the server startup process

### Added
- Added comprehensive Odoo-specific prompt to guide AI agents using the MCP interface
- Added detailed domain examples and field references in documentation

### Improved
- Enhanced tool descriptions with detailed Odoo-specific examples and documentation
- Added more robust parameter validation to prevent type mismatches
- Enriched docstrings with comprehensive Odoo domain knowledge
- Added additional parameters to tools like search_read (offset, order) for complete API coverage
- Improved error handling with more specific error messages
- Added guidance for common Odoo workflows and best practices
- Modified read_group to support empty groupby parameter for global aggregations

## [0.0.3] - 2025-03-18

### Fixed
- Fixed `OdooClient` class by adding missing methods: `get_models()`, `get_model_info()`, `get_model_fields()`, `search_read()`, and `read_records()`
- Ensured compatibility with different Odoo versions by using only basic fields when retrieving model information

### Added
- Support for retrieving all models from an Odoo instance
- Support for retrieving detailed information about specific models
- Support for searching and reading records with various filtering options

## [0.0.2] - 2025-03-18

### Fixed
- Added missing dependencies in pyproject.toml: `mcp>=0.1.1`, `requests>=2.31.0`, `xmlrpc>=0.4.1`

## [0.0.1] - 2025-03-18

### Added
- Initial release with basic Odoo XML-RPC client support
- MCP Server integration for Odoo
- Command-line interface for quick setup and testing 