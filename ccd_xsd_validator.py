"""
CCD/CDA XML Schema Validator
Validates CCD files against XSD schemas and generates detailed error reports
"""

import os
import sys
from lxml import etree
from pathlib import Path
from datetime import datetime
import argparse
import json


class CCDValidator:
    def __init__(self, xsd_path):
        """
        Initialize the validator with the main XSD schema file
        
        Args:
            xsd_path: Path to the main CDA.xsd or POCD_MT000040.xsd file
        """
        self.xsd_path = Path(xsd_path)
        self.schema = None
        self.load_schema()
    
    def load_schema(self):
        """Load the XSD schema for validation"""
        try:
            with open(self.xsd_path, 'rb') as schema_file:
                schema_doc = etree.parse(schema_file)
                self.schema = etree.XMLSchema(schema_doc)
            print(f"✓ Schema loaded successfully from: {self.xsd_path}")
        except Exception as e:
            print(f"✗ Error loading schema: {e}")
            sys.exit(1)
    
    def validate_file(self, ccd_path):
        """
        Validate a single CCD file against the schema
        
        Args:
            ccd_path: Path to the CCD XML file
            
        Returns:
            dict: Validation results with status and errors
        """
        result = {
            'file': str(ccd_path),
            'valid': False,
            'well_formed': False,
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # First check if XML is well-formed
            with open(ccd_path, 'rb') as xml_file:
                try:
                    doc = etree.parse(xml_file)
                    result['well_formed'] = True
                except etree.XMLSyntaxError as e:
                    result['errors'].append({
                        'type': 'XML_SYNTAX_ERROR',
                        'message': str(e),
                        'line': e.lineno if hasattr(e, 'lineno') else None
                    })
                    return result
            
            # Validate against schema
            if self.schema.validate(doc):
                result['valid'] = True
            else:
                # Collect all validation errors
                for error in self.schema.error_log:
                    result['errors'].append({
                        'type': 'SCHEMA_VALIDATION_ERROR',
                        'message': error.message,
                        'line': error.line,
                        'column': error.column,
                        'domain': error.domain_name,
                        'level': error.level_name
                    })
        
        except FileNotFoundError:
            result['errors'].append({
                'type': 'FILE_NOT_FOUND',
                'message': f"File not found: {ccd_path}"
            })
        except Exception as e:
            result['errors'].append({
                'type': 'UNEXPECTED_ERROR',
                'message': str(e)
            })
        
        return result
    
    def validate_directory(self, directory_path, recursive=False):
        """
        Validate all XML/CCD files in a directory
        
        Args:
            directory_path: Path to directory containing CCD files
            recursive: Whether to search subdirectories
            
        Returns:
            list: List of validation results for all files
        """
        results = []
        directory = Path(directory_path)
        
        # Find all XML files
        pattern = '**/*.xml' if recursive else '*.xml'
        xml_files = list(directory.glob(pattern))
        
        if not xml_files:
            print(f"No XML files found in {directory_path}")
            return results
        
        print(f"\nValidating {len(xml_files)} file(s)...\n")
        
        for xml_file in xml_files:
            print(f"Validating: {xml_file.name}... ", end='')
            result = self.validate_file(xml_file)
            
            if result['valid']:
                print("✓ VALID")
            elif result['well_formed']:
                print(f"✗ INVALID ({len(result['errors'])} errors)")
            else:
                print("✗ NOT WELL-FORMED")
            
            results.append(result)
        
        return results
    
    def generate_report(self, results, output_format='text', output_file=None):
        """
        Generate a validation report
        
        Args:
            results: List of validation results
            output_format: 'text', 'json', or 'html'
            output_file: Optional output file path
        """
        if output_format == 'json':
            report = self._generate_json_report(results)
        elif output_format == 'html':
            report = self._generate_html_report(results)
        else:
            report = self._generate_text_report(results)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"\nReport saved to: {output_file}")
        else:
            print(report)
        
        return report
    
    def _generate_text_report(self, results):
        """Generate a text format report"""
        lines = []
        lines.append("=" * 80)
        lines.append("CCD VALIDATION REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Total files validated: {len(results)}")
        
        valid_count = sum(1 for r in results if r['valid'])
        invalid_count = len(results) - valid_count
        
        lines.append(f"Valid: {valid_count}")
        lines.append(f"Invalid: {invalid_count}")
        lines.append("=" * 80)
        lines.append("")
        
        for result in results:
            lines.append(f"\nFile: {result['file']}")
            lines.append("-" * 80)
            
            if result['valid']:
                lines.append("Status: ✓ VALID")
            else:
                lines.append(f"Status: ✗ INVALID ({len(result['errors'])} errors)")
                lines.append("\nErrors:")
                
                for i, error in enumerate(result['errors'], 1):
                    lines.append(f"\n  Error #{i}:")
                    lines.append(f"    Type: {error['type']}")
                    lines.append(f"    Message: {error['message']}")
                    if error.get('line'):
                        lines.append(f"    Line: {error['line']}")
                    if error.get('column'):
                        lines.append(f"    Column: {error['column']}")
        
        return "\n".join(lines)
    
    def _generate_json_report(self, results):
        """Generate a JSON format report"""
        report = {
            'generated': datetime.now().isoformat(),
            'summary': {
                'total': len(results),
                'valid': sum(1 for r in results if r['valid']),
                'invalid': sum(1 for r in results if not r['valid'])
            },
            'results': results
        }
        return json.dumps(report, indent=2)
    
    def _generate_html_report(self, results):
        """Generate an HTML format report"""
        valid_count = sum(1 for r in results if r['valid'])
        invalid_count = len(results) - valid_count
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>CCD Validation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 15px; margin-bottom: 20px; }}
        .file {{ border: 1px solid #ddd; margin: 10px 0; padding: 10px; }}
        .valid {{ border-left: 5px solid #4CAF50; }}
        .invalid {{ border-left: 5px solid #f44336; }}
        .error {{ background: #ffebee; padding: 10px; margin: 5px 0; }}
        .error-type {{ font-weight: bold; color: #c62828; }}
        h1, h2 {{ color: #333; }}
    </style>
</head>
<body>
    <h1>CCD Validation Report</h1>
    <div class="summary">
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Files:</strong> {len(results)}</p>
        <p><strong>Valid:</strong> <span style="color: green;">{valid_count}</span></p>
        <p><strong>Invalid:</strong> <span style="color: red;">{invalid_count}</span></p>
    </div>
"""
        
        for result in results:
            status_class = 'valid' if result['valid'] else 'invalid'
            status_text = 'VALID' if result['valid'] else f'INVALID ({len(result["errors"])} errors)'
            status_icon = '&#x2713;' if result['valid'] else '&#x2717;'
            
            html += f"""
    <div class="file {status_class}">
        <h2>{Path(result['file']).name}</h2>
        <p><strong>Status:</strong> {status_icon} {status_text}</p>
        <p><strong>Path:</strong> {result['file']}</p>
"""
            
            if result['errors']:
                html += "        <h3>Errors:</h3>\n"
                for i, error in enumerate(result['errors'], 1):
                    location = ""
                    if error.get('line'):
                        location = f" (Line {error['line']}"
                        if error.get('column'):
                            location += f", Column {error['column']}"
                        location += ")"
                    
                    html += f"""
        <div class="error">
            <p><span class="error-type">Error #{i}: {error['type']}</span>{location}</p>
            <p>{error['message']}</p>
        </div>
"""
            
            html += "    </div>\n"
        
        html += """
</body>
</html>"""
        
        return html


def main():
    parser = argparse.ArgumentParser(
        description='Validate CCD files against XSD schema',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate a single file
  python ccd_validator.py --xsd CDA.xsd --file patient1.xml
  
  # Validate all files in a directory
  python ccd_validator.py --xsd CDA.xsd --dir ./ccd_files
  
  # Validate recursively and save HTML report
  python ccd_validator.py --xsd CDA.xsd --dir ./ccd_files --recursive --format html --output report.html
        """
    )
    
    parser.add_argument('--xsd', required=True, help='Path to main XSD schema file (e.g., CDA.xsd)')
    parser.add_argument('--file', help='Path to single CCD file to validate')
    parser.add_argument('--dir', help='Path to directory containing CCD files')
    parser.add_argument('--recursive', action='store_true', help='Search subdirectories recursively')
    parser.add_argument('--format', choices=['text', 'json', 'html'], default='text', 
                        help='Output format (default: text)')
    parser.add_argument('--output', help='Output file path (default: print to console)')
    
    args = parser.parse_args()
    
    if not args.file and not args.dir:
        parser.error('Either --file or --dir must be specified')
    
    # Create validator
    validator = CCDValidator(args.xsd)
    
    # Validate files
    if args.file:
        results = [validator.validate_file(args.file)]
    else:
        results = validator.validate_directory(args.dir, args.recursive)
    
    # Generate report
    validator.generate_report(results, args.format, args.output)
    
    # Exit with error code if any validation failed
    if any(not r['valid'] for r in results):
        sys.exit(1)


if __name__ == '__main__':
    main()
