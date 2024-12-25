from setuptools import setup, find_packages

# Read the README file for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Define required dependencies
requirements = [
    "Pillow>=9.4.0",
    "mss>=6.1.0",
    "ultralytics>=8.0.49",
    "screeninfo>=0.8.1",
    "numpy>=1.24.3",
    "requests>=2.25.1"
]

setup(
    name="yolo-overlay",  # Replace with your desired package name
    version="0.1.1",
    author="wuhp",
    author_email="your.email@example.com",
    description="A Python package to overlay YOLO detections on displays using a custom DLL.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/wuhplaptop/yolo_overlay",  # Replace with your project's URL
    packages=find_packages(include=["yolo_overlay", "yolo_overlay.*"]),
    package_data={
        'yolo_overlay': ['resources/*.dll', 'resources/*.pt'],  # Includes the DLL and model in the package
    },
    include_package_data=True,  # Ensure package data is included
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Microsoft :: Windows",
        "License :: OSI Approved :: MIT License",  # Adjust based on your license
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires='>=3.7',
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'yolo-overlay=yolo_overlay.cli:main',  # Entry point for a command-line tool
        ],
    },
    keywords="yolo overlay detection computer-vision",
)
