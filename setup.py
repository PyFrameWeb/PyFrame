"""
PyFrame - Revolutionary Full-Stack Python Web Framework

A modern web framework that lets you write React-like components in pure Python.
Build beautiful, reactive web applications without leaving Python!
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read version from package
def get_version():
    version_file = os.path.join("pyframe", "__init__.py")
    with open(version_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split('"')[1]
    return "0.1.0"

setup(
    name="pyframe-web",
    version=get_version(),
    author="PyFrame Team",
    author_email="pyframe@example.com",
    description="Revolutionary Full-Stack Python Web Framework - Write React-like components in pure Python",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/PyFrameWeb/PyFrame",
    project_urls={
        "Homepage": "https://github.com/PyFrameWeb/PyFrame",
        "Documentation": "https://github.com/PyFrameWeb/PyFrame/blob/main/README.md",
        "Bug Tracker": "https://github.com/PyFrameWeb/PyFrame/issues",
        "Source Code": "https://github.com/PyFrameWeb/PyFrame",
    },
    packages=find_packages(exclude=["tests*", "examples*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
        "Framework :: AsyncIO",
    ],
    python_requires=">=3.8",
    install_requires=[
        "websockets>=11.0.0",
        "watchdog>=3.0.0",
        "aiofiles>=23.0.0",
        "jinja2>=3.1.0",
        "click>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
        ],
        "database": [
            "sqlalchemy>=2.0.0",
            "alembic>=1.12.0",
        ],
        "cache": [
            "redis>=4.5.0",
            "memcached>=1.6.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "pyframe-web=pyframe.cli:main",
        ],
    },
    package_data={
        "pyframe": ["templates/*.html", "static/*.js", "static/*.css"],
    },
    include_package_data=True,
    zip_safe=False,
    keywords=[
        "web framework", "python", "react", "components", "frontend", "backend", 
        "full-stack", "reactive", "hot-reload", "transpiler", "javascript"
    ],
)
