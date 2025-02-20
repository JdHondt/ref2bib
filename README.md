# Reference to BibTeX Converter

A Python tool that converts academic references to BibTeX entries using the Crossref API.

## Installation

1. Clone this repository
2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Create a text file with your references, one per line
2. Run the script:
   ```bash
   python ref2bib.py input_references.txt -o output.bib
   ```

### Optional Arguments

- `--output` or `-o`: Specify output file (default: references.bib)
- `--api-key`: Provide a Crossref API key for better rate limits

## Example

Input file (`references.txt`):
```
[1] Smith, J. (2020). Machine Learning Basics. Journal of AI, 
    15(2), 123-145.
[2] Johnson, R. and Williams, P. (2019). Deep Learning 
    Applications in Time Series Analysis. Conference on 
    Neural Networks, pp. 45-67.
```

Run:
```bash
python ref2bib.py references.txt
```

Output will be saved in `references.bib` in BibTeX format.

## Limitations

- Requires internet connection to access Crossref API
- Reference matching accuracy depends on Crossref's search capabilities
- Some references might not be found or might be matched incorrectly
