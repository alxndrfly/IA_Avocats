# Changelog

## [Version 4.0.0] - 2024-11-19
### Added
- Generateur de résumés avec bordeaux now works with images/photos :
  - Classifies pages by type (TEXT, IMAGE, SKIP)
  - Describes images using GPT-4o

- Résumé de document PDF ou Word adjusts it's output to the size of the text :
  - Chunking summary API requests with a set token size
  - Allows for longer documents to be summarized correctly

- New sidebar layout

- Improved instructions and readability of each functionality

### Fixed
- PDF to Word conversion now uses adobe API to get a good PDF to Word conversion


## [Version 3.0.0] - 2024-11-11
### Added
- New feature: Organizes summaries by chronological order


## [Version 2.0.0] - 2024-11-08
### Fixed
- Improved accessibility by adding proper labels to file uploaders
- Fixed empty label warnings in console

### Added
- New feature (To improve later): PDF to Word conversion
  - OCR-based conversion preserving layout (not perfect yet)
  - Support for multi-page documents
  - Direct Word document download

- New feature: Single Document Summary
  - Support for both PDF and Word documents
  - Smart text extraction (OCR for PDFs, native for Word)
  - Customized summary generation with GPT
  - Download options in both .txt and .docx formats
  - Document name preservation in outputs

### Improved
- Summary generator of legal documents now generates a 'bordereau' of each legal document.


## [Version 1.0.0] - 2024-10-25
### Initial Release
- Basic app, one feature:
- Extract text from PDFs, summarize and format for legal conclusions