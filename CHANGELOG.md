# Changelog
## [Version 3.0.0] - 2024-11-08
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