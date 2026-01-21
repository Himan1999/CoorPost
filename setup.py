from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="coorpost",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Coordinated Post Detection for Facebook and Social Media",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/CoorPost",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=1.3.0",
        "numpy>=1.20.0",
        "networkx>=2.6.0",
        "matplotlib>=3.4.0",
        "pillow>=8.0.0",
        "imagehash>=4.2.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "pytest-cov>=2.12.0",
            "flake8>=3.9.0",
            "black>=21.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "coorpost=coorpost.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "coorpost": ["data/*.csv"],
    },
)
