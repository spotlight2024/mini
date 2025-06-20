from setuptools import setup, find_packages

setup(
    name="websocket-service",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "websockets>=10.0",
        "pytest>=6.2.5",
        "pytest-asyncio>=0.16.0",
        "httpx>=0.23.0",
    ],
    python_requires=">=3.7",
) 