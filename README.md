# Office Space Calculator

A comprehensive office space programming tool for architecture firms. Calculate space requirements based on staff counts, departmental needs, and industry-standard space allocations.

## Features

- **Staff & Department Management**: Register companies, add departments, and define staff positions with specific workspace types
- **Industry-Standard Space Calculations**: Built-in standards for offices, workstations, meeting rooms, and support spaces
- **Circulation Factor**: Apply industry-standard circulation factors (25-35%) to calculate total usable area
- **Loss/Add-on Factor**: Convert usable SF to rentable SF using building efficiency factors
- **Remote Work Analysis**: Analyze how different remote work policies affect space requirements
- **Multiple Export Formats**: Generate reports in PDF, Excel (.xlsx), or both
- **Data Persistence**: Save and load projects for future adjustments

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd office-space-calculator

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

## Quick Start

### Quick Estimate
For a fast calculation without saving:
```bash
python -m src.cli quick
```

### Full Project Workflow

1. **Create a new project**:
```bash
python -m src.cli new --name "Acme Corporation" --location "New York, NY"
```

2. **Add departments and staff**:
```bash
python -m src.cli add-dept <project-id> --name "Engineering"
```

3. **Auto-allocate support spaces**:
```bash
python -m src.cli auto-support <project-id>
```

4. **Calculate space requirements**:
```bash
python -m src.cli calculate <project-id>
```

5. **Analyze remote work impact**:
```bash
python -m src.cli remote-analysis <project-id>
```

6. **Export reports**:
```bash
python -m src.cli export <project-id> --format all --include-remote
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `new` | Create a new space programming project |
| `list` | List all saved projects |
| `load <id>` | Display project details |
| `add-dept <id>` | Add a department to a project |
| `add-staff <id> <dept>` | Add staff to a department |
| `auto-support <id>` | Auto-allocate support spaces based on headcount |
| `calculate <id>` | Calculate space requirements |
| `remote-analysis <id>` | Analyze remote work impact |
| `export <id>` | Export to PDF/Excel |
| `settings <id>` | Update calculation settings |
| `standards` | Display standard space sizes |
| `quick` | Quick interactive calculation |
| `delete <id>` | Delete a project |

## Space Types

### Individual Workspaces
- **Large Private Office**: 225 SF (Executives)
- **Medium Private Office**: 150 SF (Managers)
- **Small Private Office**: 100 SF (Professionals)
- **Large Workstation**: 80 SF (8x10)
- **Standard Workstation**: 64 SF (8x8)
- **Compact Workstation**: 48 SF (6x8)
- **Hoteling Station**: 42 SF (Shared)

### Meeting Spaces
- **Large Conference**: 600 SF (16-20 people)
- **Medium Conference**: 300 SF (10-12 people)
- **Small Conference**: 150 SF (6-8 people)
- **Huddle Room**: 80 SF (3-4 people)
- **Phone Booth**: 35 SF (1 person)

### Support Spaces
- Reception, Waiting Area, Break Room, Kitchen
- Copy/Print, Mail Room, Storage, Server Room
- Wellness Room, Training Room, Focus Rooms
- Collaboration Areas

## Calculation Methodology

### Usable Square Footage
```
Net Usable SF = Workspace SF + Meeting SF + Support SF
Circulation SF = Net Usable SF × Circulation Factor
Usable SF = Net Usable SF + Circulation SF
```

### Rentable Square Footage
```
Rentable SF = Usable SF × (1 + Loss Factor)
```

### Industry Standards
- **Circulation Factor**: 25-35% (default 30%)
- **Loss Factor**: 10-20% (varies by building class)

## Remote Work Analysis

The tool includes pre-defined scenarios to analyze space reduction potential:

| Scenario | Remote % | Potential Reduction |
|----------|----------|---------------------|
| Traditional | 0% | 0% |
| Minimal Remote | 20% | 10% |
| Hybrid Balanced | 50% | 30% |
| Heavy Remote | 70% | 50% |
| Remote First | 85% | 65% |
| Fully Remote | 95% | 80% |

## Data Storage

Projects are saved as JSON files in the `data/projects/` directory. Each project can be loaded, modified, and recalculated at any time.

## Export Formats

### PDF Report
- Executive summary
- Department breakdown
- Space type allocation
- Meeting and support space details
- Remote work analysis (optional)

### Excel/XLSX
- Multiple worksheets for different views
- Summary, Departments, Space Breakdown
- Space Standards reference
- Remote Work Analysis (optional)

## License

MIT License
