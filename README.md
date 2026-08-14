# ece-652-take-home-final

> **Student Name**: Samuel Street
>
> **Student ID**: sstreet
>
> **Student No.**: 20825395

## Overview

This repository contains the code submission for the ECE 652 take-home final. Please note that there is a test framework that is configured with the code but it uses Pytest. These additional dependencies are **not** required to run the command line tool as specified in the assessment instructions and are commented out in the requirements.

Please further note that to match behavior of Cheddar, I first choose the available task instances with pending execution with the same lowest relative deadline. If there is one then there's no ambiguity in which should execute first. If there are more than one, Cheddar seems to select the one with the largest period which I have also used in the implementation in this submission.

## Test Cases

If you wish to run all the addiitonal test cases, uncomment the lines and reinstall the additional packages and then run the following command in the root directory of this repository (as the test files need access to the Python files containing the scheduler implementation).

```bash
PYTHONPATH="$(pwd)" pytest
```