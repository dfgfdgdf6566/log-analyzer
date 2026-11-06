#!/bin/bash
pytest --cov=. --cov-report=term-missing --cov-report=html test_main.py
