# Agent Instructions

Use the project conda environment for Python commands.

```bash
conda run -n book-inventory <command>
```

Run tests with coverage before finishing code changes:

```bash
conda run -n book-inventory pytest
```

Prefer the Makefile shortcuts when available:

```bash
make test
```
