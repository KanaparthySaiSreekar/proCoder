# Publishing proCoder to PyPI

This guide explains how to publish proCoder to the Python Package Index (PyPI) so users can install it with a simple `pip install procoder-ai` command.

## Prerequisites

1. **PyPI Account**
   - Create an account at https://pypi.org/account/register/
   - Verify your email address

2. **PyPI API Token**
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token
   - Scope: "Entire account" (for first upload) or "Project: proCoder-ai" (for updates)
   - Save the token securely (starts with `pypi-`)

3. **Install Build Tools**
   ```bash
   pip install --upgrade build twine
   ```

## Publishing Steps

### 1. Prepare the Release

Update version numbers and ensure everything is ready:

```bash
# Update version in setup.py
# Current: version='0.4.0'

# Create a git tag for the release
git tag -a v0.4.0 -m "Release v0.4.0: Easy installation with one-line commands"
git push origin v0.4.0
```

### 2. Clean Previous Builds

Remove any old build artifacts:

```bash
rm -rf dist/ build/ *.egg-info
```

### 3. Build the Package

Create source distribution and wheel:

```bash
python -m build
```

This creates:
- `dist/proCoder-ai-0.4.0.tar.gz` (source distribution)
- `dist/proCoder_ai-0.4.0-py3-none-any.whl` (wheel)

### 4. Test the Build

Verify the package contents:

```bash
# Check package contents
tar -tzf dist/proCoder-ai-0.4.0.tar.gz

# Test installation locally
pip install dist/proCoder-ai-0.4.0.tar.gz
proCoder --help
pip uninstall proCoder-ai
```

### 5. Upload to TestPyPI (Optional but Recommended)

Test the upload process on TestPyPI first:

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ procoder-ai

# Test it works
proCoder --help

# Uninstall test version
pip uninstall proCoder-ai
```

### 6. Upload to PyPI

Once everything works on TestPyPI, upload to the real PyPI:

```bash
twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token (paste the full token including `pypi-` prefix)

### 7. Verify the Upload

Check your package on PyPI:
- https://pypi.org/project/proCoder-ai/

Test installation:
```bash
pip install procoder-ai
proCoder setup
```

## Future Updates

For subsequent releases:

1. **Update Version**
   ```bash
   # Edit setup.py - increment version (e.g., 0.4.0 -> 0.4.1 or 0.5.0)
   ```

2. **Update Changelog**
   - Document changes in README.md under "Recent Updates"

3. **Commit Changes**
   ```bash
   git add setup.py README.md
   git commit -m "Bump version to 0.4.1"
   git push
   ```

4. **Create Tag**
   ```bash
   git tag -a v0.4.1 -m "Release v0.4.1: Bug fixes and improvements"
   git push origin v0.4.1
   ```

5. **Build and Upload**
   ```bash
   rm -rf dist/ build/ *.egg-info
   python -m build
   twine upload dist/*
   ```

## Semantic Versioning

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR** version (1.0.0): Incompatible API changes
- **MINOR** version (0.5.0): New functionality, backwards-compatible
- **PATCH** version (0.4.1): Bug fixes, backwards-compatible

Current: **0.4.0** (Beta - stable but may have minor changes)

When to increment:
- `0.4.0 -> 0.4.1`: Bug fixes only
- `0.4.0 -> 0.5.0`: New features added
- `0.4.0 -> 1.0.0`: Stable release, production-ready

## Troubleshooting

### Issue: "Package already exists"

The version you're trying to upload already exists on PyPI. You must increment the version number in `setup.py`.

```bash
# Increment version
vim setup.py  # Change version='0.4.0' to version='0.4.1'
rm -rf dist/
python -m build
twine upload dist/*
```

### Issue: "Invalid authentication credentials"

Your PyPI token is incorrect or expired.

```bash
# Use username: __token__
# Password: pypi-... (full token with prefix)

# Or configure in ~/.pypirc:
cat > ~/.pypirc << EOF
[pypi]
  username = __token__
  password = pypi-YourTokenHere
EOF
chmod 600 ~/.pypirc
```

### Issue: "Distribution already exists"

Clean your dist directory and rebuild:

```bash
rm -rf dist/ build/ *.egg-info
python -m build
```

### Issue: Package description rendering error

Validate your README.md:

```bash
pip install readme-renderer
python -m readme_renderer README.md
```

## Automation with GitHub Actions (Optional)

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: twine upload dist/*
```

Add your PyPI token to GitHub secrets as `PYPI_API_TOKEN`.

## After Publishing

Update documentation:

1. **README.md** - Add pip install instruction:
   ```markdown
   ## Quick Install

   ```bash
   pip install procoder-ai
   ```

2. **Update install scripts** - Prefer PyPI over git:
   ```bash
   pip install --user procoder-ai
   # Instead of: pip install --user git+https://...
   ```

3. **Announce the release**:
   - GitHub Releases page
   - Social media
   - Dev.to or Medium blog post

## Resources

- [PyPI Documentation](https://packaging.python.org/tutorials/packaging-projects/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)
- [Python Packaging Guide](https://packaging.python.org/)
