"""Enables ``python -m investment.cli`` as an alternative to the
``investment-python`` console script.
"""
from investment.cli.main import main

if __name__ == "__main__":
    main()
