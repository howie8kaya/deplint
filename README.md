# deplint

Static analysis tool for Python dependency files that detects version conflicts and outdated pinned packages.

## Installation

```bash
pip install deplint
```

## Usage

Run `deplint` against your requirements file:

```bash
deplint requirements.txt
```

Example output:

```
requirements.txt
  [CONFLICT]  boto3==1.24.0 conflicts with botocore>=1.27.60 (required by s3transfer)
  [OUTDATED]  requests==2.28.0  →  2.31.0
  [OUTDATED]  django==3.2.0  →  3.2.20

2 outdated, 1 conflict found.
```

You can also lint multiple files at once:

```bash
deplint requirements/*.txt
```

To check only for conflicts or only for outdated packages:

```bash
deplint --only conflicts requirements.txt
deplint --only outdated requirements.txt
```

Exit code is non-zero when issues are found, making it easy to integrate into CI pipelines:

```yaml
# .github/workflows/lint.yml
- name: Check dependencies
  run: deplint requirements.txt
```

## Supported File Formats

- `requirements.txt`
- `requirements-*.txt`
- `constraints.txt`

## License

MIT