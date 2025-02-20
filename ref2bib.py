import time
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import argparse
import sys
from typing import List, Optional

class Reference2BibTeX:
    def __init__(self, api_key: Optional[str] = None, email: str = 'your.email@example.com'):
        self.crossref_api = "https://api.crossref.org/works"
        self.headers = {
            'User-Agent': f'Reference2BibTeX/1.0 (https://github.com/JdHondt/ref2bib; mailto:{email})'
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
            time.sleep(.5)  # Wait .5 seconds between requests
            
            if response.status_code == 200:
                data = response.json()
                if data['message']['items']:
                    return data['message']['items'][0]
            else:
                print(f"API request failed with status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {str(e)}")
        return {}

    def _escape_tex(self, text: str) -> str:
        """Escape special characters for BibTeX"""
        replacements = {
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
            '\\': r'\textbackslash{}',
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text

    def to_bibtex(self, crossref_data: dict) -> str:
        """Convert Crossref data to BibTeX entry"""
        if not crossref_data:
            return ""

        # Get the entry type
        entry_type = crossref_data.get('type', 'article')

        # Create ID from first author's last name and year
        year = str(crossref_data.get('published-print', {}).get('date-parts', [['']])[0][0])
        year_suffix = year[-2:] if year else ''
        
        first_author = crossref_data.get('author', [{}])[0]
        author_lastname = first_author.get('family', '').lower() if first_author else ''
        entry_id = f"{author_lastname}{year_suffix}" if author_lastname and year_suffix else crossref_data.get('DOI', '').replace('/', '_')

        # Prepare the fields
        fields = {
            'title': '{' + self._escape_tex(crossref_data.get('title', [''])[0]) + '}',
            'author': '{' + self._escape_tex(' and '.join([
                f"{author.get('family', '')}, {author.get('given', '')}"
                for author in crossref_data.get('author', [])
            ])) + '}',
            'year': str(crossref_data.get('published-print', {}).get('date-parts', [['']])[0][0]),
            'doi': crossref_data.get('DOI', ''),
        }

        # Add optional fields
        if 'container-title' in crossref_data and crossref_data['container-title']:
            fields['journal'] = '{' + self._escape_tex(crossref_data['container-title'][0]) + '}'
        if 'volume' in crossref_data:
            fields['volume'] = str(crossref_data['volume'])
        if 'issue' in crossref_data:
            fields['number'] = str(crossref_data['issue'])
        if 'page' in crossref_data:
            fields['pages'] = str(crossref_data['page'])

        # Build the BibTeX entry
        bibtex = [f"@{entry_type}{{{entry_id},"]
        for key, value in fields.items():
            if value:  # Only include non-empty fields
                bibtex.append(f"  {key} = {value},")
        bibtex.append("}")

        return '\n'.join(bibtex)

    def convert_references(self, references: List[str], output_file: str) -> int:
        """Convert references to BibTeX entries and write them to file"""
        successful_conversions = 0
        total = len(references)
        
        print(f"Converting {total} references...")
        for i, ref in enumerate(references, 1):
            print(f"Processing reference {i}/{total}: {ref[:100]}")
            try:
                crossref_data = self.search_reference(ref)
                bibtex = self.to_bibtex(crossref_data)
                if bibtex:
                    print("✓ Match found")
                    # Open and close file for each entry
                    with open(output_file, 'a', encoding='utf-8') as f:
                        f.write(bibtex + "\n\n")
                    successful_conversions += 1
                else:
                    print("✗ No match found")
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                continue
        
        print(f"\nSummary: Successfully converted {successful_conversions} out of {total} references")
        return successful_conversions

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
    parser.add_argument('--output', '-o', help='Output file for BibTeX entries', default=None)
    parser.add_argument('--api-key', help='Crossref API key (optional)', default=None)
    parser.add_argument('--email', help='Email for API identification', default='your.email@example.com')
    
    args = parser.parse_args()

    # If no output file is specified, use the input file name with .bib extension
    if not args.output:
        args.output = args.input_file.replace('.txt', '.bib')

    try:
        # Read the entire file content
        with open(args.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse the references
        references = parse_numbered_references(content)
        print(f"Found {len(references)} references in the input file")

        converter = Reference2BibTeX(args.api_key, args.email)
        successful = converter.convert_references(references, args.output)

        if successful > 0:
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
        sys.argv.extend(["paparrizos20_small.txt"])

    main()
