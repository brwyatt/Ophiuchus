# Ophiuchus
Library to create, build, and deploy serverless website stacks on AWS

**NOTE: This project is currently under heavy development and should be considered experimental**

## Related Repos

* [Ophiuchus-Demo](https://github.com/brwyatt/Ophiuchus-Demo): Demo site built with Ophiuchus
* [Ophiuchus-Template](https://github.com/brwyatt/Ophiuchus-Template): Template repo to setup an Ophiuchus-based site

## Development

### Setup

1. Create Python Virtual Environment:
   `python3 -m venv env`
2. Activate Python venv:
   `source env/bin/activate`
3. Install dev tools:
   `pip3 install -r requirements-dev.txt`
4. Install pre-commit hooks:
   `pre-commit install`

### Development

Edit files as usual.

If the pre-commit hooks are installed, formatting and style will be checked and applied before committing. If not installed, run formatters manually prior to submitting a Pull Request to ensure consistency across the project.
