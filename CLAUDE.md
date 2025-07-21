# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SpotLight is a hybrid automation platform for Android virtual machines that supports WeChat mini-programs, WebView, and native automation with multi-device concurrency, intelligent commands, popup handling, and data collection capabilities.

The codebase follows a layered architecture:
- **Android APP (aidaemon)** ↔ **Hybrid Driver Service** ↔ **Hybrid WebDriver (Selenium/Appium)** ↔ **WeChat Mini-programs/WebView**

## Development Commands

### Service Management
```bash
# Start service
./start.sh start

# Stop service  
./start.sh stop

# Check service status
./start.sh status

# Restart service
./start.sh restart

# View logs
./start.sh logs

# View logs in real-time
./start.sh logs -f
```

### Development & Testing
```bash
# Install dependencies
./start.sh install

# Run all tests
./start.sh test
# OR
python3 -m pytest tests/ -v

# Clean cache files
./start.sh clean

# Use CLI tools
./start.sh cli status
```

### Virtual Environment
```bash
# Activate virtual environment
source .venv/bin/activate
# OR
source activate_venv.sh
```

## Core Architecture

### Device Management Layer
- **DevicePool**: Singleton pattern device pool manager with thread-safe multi-device concurrency, automatic cleanup, and LRU resource recycling
- **AndroidDevice**: Device abstraction providing unified interface for ADB connections, WebDriver management, element operations

### Hybrid WebDriver Execution Layer  
- **WebExecutor Interface**: Abstract interface defining WebDriver implementation contracts
- **SeleniumExecutor**: Selenium-based WebDriver for web automation
- **AppiumExecutor**: Appium-based WebDriver for native app automation
- **PopupHandler**: Intelligent popup detection and handling system
- **WaitUtils**: Advanced wait conditions and strategies

### Operation System Layer
- **OperationSequence**: Chain-of-responsibility pattern for complex operation sequences
- **Operation Types**: FindElement, Click, Wait, JS execution, HandlePopup, CollectItems
- **Protocol Mapping**: Supports both legacy and new protocol formats for compatibility

### Service Layer
- **FastAPI Server**: REST API service at `hybrid_driver/server.py`
- **WebSocket Support**: Real-time communication capabilities
- **Request Models**: Pydantic models for API validation (ConnectRequest, ActionRequest, etc.)

## Key Design Patterns

1. **Singleton Pattern**: DevicePool ensures global device management
2. **Abstract Factory**: WebExecutor implementations (Selenium/Appium)
3. **Chain of Responsibility**: OperationSequence for complex workflows
4. **Context Manager**: AndroidDevice supports `with` statements for resource management
5. **Strategy Pattern**: Different wait conditions and popup handling strategies

## File Structure

- `hybrid_driver/` - Core service implementation
- `scripts/` - Service management and CLI tools
- `tests/` - Unit and integration tests
- `docs/` - Comprehensive documentation
- `config/` - Configuration files
- `requirements/` - Dependency management

## Testing Configuration

Tests use pytest with logging enabled (see `hybrid_driver/pytest.ini`). Test fixtures available in `tests/fixtures/` for HTML test cases.

## Important Notes

- No linting tools configured - code formatting follows existing patterns
- Service runs on configurable ports (default: 8002 for server, 6524 for WebSocket)
- Supports both Chinese and English documentation
- Device connections managed through ADB with automatic cleanup
- WebDriver sessions pooled for performance optimization