from setuptools import setup, find_packages
import os

# Read the README file for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="yolo-overlay",  # Replace with your desired package name
    version="0.1.0",
    author="wuhp",
    author_email="your.email@example.com",
    description="A Python package to overlay YOLO detections on displays using a custom DLL.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wuhplaptop/yolo_overlay",  # Replace with your project's URL
    packages=find_packages(),
    package_data={
        'yolo_overlay': ['resources/*.dll'],  # This will now include overlay-yolo.dll
    },
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
        "License :: OSI Approved :: MIT License",  # Choose your license
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3.7',
    install_requires=[
        "Pillow",
        "mss",
        "ultralytics",
        "screeninfo",
        "numpy",
    ],
    entry_points={
        'console_scripts': [
            'yolo-overlay=yolo_overlay.cli:main',
        ],
    },
)
