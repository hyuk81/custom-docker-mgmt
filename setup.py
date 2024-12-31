from setuptools import setup, find_packages

setup(
    name="docker-mgmt",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "typer",
        "rich",
        "docker",
        "textual",
    ],
    entry_points={
        "console_scripts": [
            "docker-mgmt=docker_mgmt.__main__:app",
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A comprehensive Docker management tool",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/docker-mgmt",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
) 