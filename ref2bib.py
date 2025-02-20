import time
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import bibtexparser
import argparse
import sys
import json
from typing import List, Optional

class Reference2BibTeX:
    def __init__(self, api_key: Optional[str] = None):
        self.crossref_api = "https://api.crossref.org/works"
        self.headers = {
            'User-Agent': 'Reference2BibTeX/1.0 (https://github.com/yourusername/ref2bib; mailto:j.e.d.hondt@tue.nl)'
        }
        if api_key:
            self.headers['Authorization'] = f'Bearer {api_key}'

        # Add retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        self.session = requests.Session()
        self.session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
        
    def search_reference(self, reference: str) -> dict:
        """Search for a reference using Crossref API"""
        params = {
            'query': reference,
            'rows': 1
        }
        try:
            response = self.session.get(
                self.crossref_api, 
                params=params, 
                headers=self.headers,
                timeout=10
            )
            # Add rate limiting
            time.sleep(1)  # Wait 1 second between requests
            
            if response.status_code == 200:
                data = response.json()
                if data['message']['items']:
                    return data['message']['items'][0]
            else:
                print(f"API request failed with status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
        return {}

    def to_bibtex(self, crossref_data: dict) -> str:
        """Convert Crossref data to BibTeX entry"""
        if not crossref_data:
            return ""

        entry = {
            'ID': crossref_data.get('DOI', '').replace('/', '_'),
            'ENTRYTYPE': crossref_data.get('type', 'article'),
            'title': crossref_data.get('title', [''])[0],
            'author': ' and '.join([f"{author.get('family', '')}, {author.get('given', '')}" 
                                  for author in crossref_data.get('author', [])]),
            'year': str(crossref_data.get('published-print', {}).get('date-parts', [['']])[0][0]),
            'doi': crossref_data.get('DOI', ''),
        }

        if 'container-title' in crossref_data:
            entry['journal'] = crossref_data['container-title'][0]

        return bibtexparser.dumps(bibtexparser.bibdatabase.BibDatabase(entries=[entry]))

    def convert_references(self, references: List[str]) -> List[str]:
        """Convert a list of references to BibTeX entries"""
        bibtex_entries = []
        total = len(references)
        
        print(f"Converting {total} references...")
        for i, ref in enumerate(references, 1):
            print(f"Processing reference {i}/{total}", end='\r')
            try:
                crossref_data = self.search_reference(ref)
                bibtex = self.to_bibtex(crossref_data)
                if bibtex:
                    print("✓ Match found")
                    bibtex_entries.append(bibtex)
                else:
                    print("✗ No match found")
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                continue
        
        print(f"\nSummary: Successfully converted {len(bibtex_entries)} out of {total} references")
        return bibtex_entries

def parse_numbered_references(content: str) -> List[str]:
    """Parse numbered references from text content."""
    # Split by reference number pattern [n]
    import re
    
    # Split the content by reference numbers and keep the numbers
    parts = re.split(r'(\[\d+\])', content)
    
    # Remove empty strings and whitespace-only strings
    parts = [p.strip() for p in parts if p.strip()]
    
    references = []
    current_ref = ""
    
    for part in parts:
        if re.match(r'\[\d+\]', part):
            if current_ref:  # Save previous reference if exists
                references.append(current_ref.strip())
            current_ref = ""
        else:
            # Replace line breaks with spaces and normalize whitespace
            cleaned_part = ' '.join(part.split())
            current_ref += " " + cleaned_part if current_ref else cleaned_part
    
    # Add the last reference
    if current_ref:
        references.append(current_ref.strip())
    
    return references

def main():
    parser = argparse.ArgumentParser(description='Convert academic references to BibTeX entries')
    parser.add_argument('input_file', help='File containing numbered references')
    parser.add_argument('--output', '-o', help='Output file for BibTeX entries', default='references.bib')
    parser.add_argument('--api-key', help='Crossref API key (optional)', default=None)
    
    args = parser.parse_args()

    try:
        # Read the entire file content
        with open(args.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the references
        references = parse_numbered_references(content)
        print(f"Found {len(references)} references in the input file")

        converter = Reference2BibTeX(args.api_key)
        bibtex_entries = converter.convert_references(references)

        if bibtex_entries:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(bibtex_entries))
            print(f"BibTeX entries written to {args.output}")
        else:
            print("No BibTeX entries were generated")

    except FileNotFoundError:
        print(f"Error: Input file '{args.input_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    # Manual run
    if len(sys.argv) == 1:
        sys.argv.extend(["ref2bib/paparrizos20.txt", "--output", "ref2bib/paparrizos20.bib"])

    main()
