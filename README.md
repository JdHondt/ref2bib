# ref2bib

Convert numbered references from text files to BibTeX entries using the Crossref API.

## Features

- Parse numbered references from text files (e.g., [1], [2], etc.)
- Search references using Crossref API
- Generate BibTeX entries with proper formatting
- Support for rate limiting and retry strategies
- Continuous file writing (resilient to interruptions)
- Customizable email for API identification

## Installation

1. Clone the repository:
```bash
git clone https://github.com/JdHondt/ref2bib.git
cd ref2bib
```

2. Install dependencies:
```bash
pip install requests
```

## Usage

Basic usage:
```bash
python ref2bib.py input.txt
```

With options:
```bash
python ref2bib.py input.txt --output references.bib --email your.email@example.com --api-key YOUR_API_KEY
```

### Options

- `input_file`: Text file containing numbered references
- `--output`, `-o`: Output BibTeX file (default: input filename with .bib extension)
- `--email`: Email for API identification (recommended)
- `--api-key`: Crossref API key (optional)

### Input Format

The input file should contain numbered references in the format:

```
[1] Author, Title, Journal, Year
[2] Another reference
```

### Output

The script generates BibTeX entries with the following features:
- Citation keys based on first author's last name and year (e.g., smith21)
- Properly escaped special characters
- Essential fields (title, author, year, doi)
- Optional fields (journal, volume, number, pages)

## Example

Input (`sample.txt`):
```
[1] Abanda, A., Mori, U., & Lozano, J. A. (2019). A review on distance based time series classification. Data Mining and Knowledge Discovery, 33(2), 378-412.
```

Output (`sample.bib`):
```bibtex
@article{abanda19,
  title = {A review on distance based time series classification},
  author = {Abanda, Amaia and Mori, Usue and Lozano, Jose A.},
  year = 2019,
  journal = {Data Mining and Knowledge Discovery},
  volume = 33,
  number = 2,
  pages = 378-412,
  doi = 10.1007/s10618-018-0596-4
}
```

## License

MIT License
