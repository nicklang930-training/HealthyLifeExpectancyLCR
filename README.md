# \# HealthyLifeExpectancyLCR

# 

This project downloads, filters, and republishes Healthy Life Expectancy (HLE) data for the Liverpool City Region (LCR) local authorities sourced from the Office for National Statistics (ONS).

===

# The data shows the number of years people are expected to spend in “good” general health in these areas as well as the average in England and Wales.

# 

# \## The process does the following:

# 

\- Downloads the latest UK health state life expectancy dataset from ONS
- There are two sheets of data:
	- Healthy Life Expectancy between 2011 \& 2023
	- The change in Healthy Life Expectancy between 2011 \& 2023
===

# \- Filters it down to the Liverpool City Region local authority areas 

# &#x20; (Liverpool, Knowsley, Sefton, St Helens, Wirral, Halton) plus England and Wales 

# &#x20; comparators

# \- Filters to the under-1 age group

\- Outputs the results of the two sheets as:
	- HealthyLifeExpectancyLCR.xlsx
	- ChangeInHealthyLifeExpectancyLCR.xlsx
===

# \## Data

# 

# See \[DATA\_LICENSE.md](DATA\_LICENSE.md) for source and licensing information.

# 

# \## Running this project

# 

This project uses \[uv](https://docs.astral.sh/uv/) for dependency management.

uv sync
===

uv run main.py

This will download the source file, filter it, and produce the two outputs:
===



&#x09;- HealthyLifeExpectancyLCR.xlsx
	- ChangeInHealthyLifeExpectancyLCR.xlsx
===



