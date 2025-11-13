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
    'tiktoken>=0.5.0', # For accurate token counting
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
    version='0.4.0',   # Added multi-model switching, persistent memory, OpenRouter integration
    author='Kanaparthy Sai Sreekar',
    author_email='kanapasai@gmail.com',
    description='Professional AI coding assistant for your terminal - multi-model switching, persistent memory, and OpenRouter integration',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/KanaparthySaiSreekar/proCoder',
    project_urls={
        'Bug Tracker': 'https://github.com/KanaparthySaiSreekar/proCoder/issues',
        'Documentation': 'https://github.com/KanaparthySaiSreekar/proCoder#readme',
        'Source Code': 'https://github.com/KanaparthySaiSreekar/proCoder',
    },
    license='MIT',
    packages=find_packages(exclude=['tests', 'tests.*']), # Finds the 'proCoder' package automatically
    include_package_data=True, # Include non-code files listed in MANIFEST.in (if any)
    install_requires=INSTALL_REQUIRES,
    entry_points={
        'console_scripts': [
            # This creates the `proCoder` command in the system path upon installation
            'proCoder = proCoder.main:run',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta', # v0.4.0 is stable beta
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Software Development',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Quality Assurance',
        'Topic :: Terminals',
        'Topic :: Utilities',
        'Natural Language :: English',
    ],
    keywords='ai coding assistant cli terminal openrouter anthropic claude gpt code-editor developer-tools',
    python_requires='>=3.8',
)