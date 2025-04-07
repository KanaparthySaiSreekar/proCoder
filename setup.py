from setuptools import setup, find_packages
import os

# Function to read requirements from a file
def load_requirements(filename='requirements.txt'):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

# Basic dependencies (add others if needed, e.g., specific linters)
# Note: GitPython is NOT included, assuming git CLI is available.
# If you want GitPython, add 'GitPython' here and update git_utils.py
INSTALL_REQUIRES = [
    'openai>=1.10.0,<2.0.0', # For OpenRouter interaction via OpenAI library interface
    'python-dotenv>=1.0.0',
    'typer[all]>=0.9.0', # Includes rich
    'rich>=13.0.0',
    # requests is usually a sub-dependency of openai, but can list explicitly
    'requests>=2.20.0',
    # beautifulsoup4/lxml might be needed if markdown parsing of code blocks fails often
    # 'beautifulsoup4',
    # 'lxml',
]

# Read long description from README.md if it exists
long_description = ""
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()

setup(
    name='proCoder-ai', # Package name on PyPI
    version='0.2.0',   # Increment version for new features
    author='Your Name / Your Org', # Change this
    author_email='your.email@example.com', # Change this
    description='An AI coding assistant for your terminal powered by OpenRouter.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/yourusername/proCoder-project', # Change this
    license='MIT', # Or choose another license
    packages=find_packages(), # Finds the 'proCoder' package automatically
    include_package_data=True, # Include non-code files listed in MANIFEST.in (if any)
    install_requires=INSTALL_REQUIRES,
    entry_points={
        'console_scripts': [
            # This creates the `proCoder` command in the system path upon installation
            'proCoder = proCoder.main:run',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha', # Change as appropriate
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License', # Match license above
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
        'Topic :: Terminals',
        'Topic :: Utilities',
    ],
    python_requires='>=3.8', # Set minimum Python version
)