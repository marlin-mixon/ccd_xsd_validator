# ccd_xsd_validator
Validates a single ccd or a directory of ccds against your xsd.

## Setup

1. Clone this repository
2. Skip this step to use the provided xsd.  Otherwise, download CDA schemas and place in a directory.
3. Run validation:
```bash
   python ccd_xsd_validator.py --xsd CDA-core-2.0-master/schema/extensions/SDTC/infrastructure/cda/CDA_SDTC.xsd --dir ./your_ccds
```
