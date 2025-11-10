
## Step 1: Check if Python is Installed

Open Command Prompt (cmd) and run:

```cmd
python --version
```

**Expected output**: `Python 3.x.x` (e.g., Python 3.12.6)
If you don't have Python, download it from: https://www.python.org/downloads/

---
## Step 2: Navigate to Your Project Folder

```cmd
cd /d "c:\Users\twan\OneDrive - Danmarks Tekniske Universitet\Desktop\H4\2. MachineLearning\2.1ExampleProject"
```
---
## Step 3: Create Virtual Environment

```cmd
python -m venv .venv
```

This creates a folder called `.venv` with Python environment.

---
## Step 4: Activate Virtual Environment

```cmd
.venv\Scripts\activate
```
You should see `(.venv)` appear before your command prompt.

---
## Step 5: Install All Required Libraries
```cmd
pip install numpy pandas matplotlib scikit-learn joblib
```
---
## Step 6: Verify Installation

```cmd
python -c "import numpy, pandas, matplotlib, sklearn, joblib; print('All libraries installed successfully!')"
```
---
## Step 7: Run the Program
```cmd
python Salary_Analysis.py
```
---
## 📋 Complete Command List (Copy & Paste)

  ```cmd

REM Step 1: Navigate to project

cd /d "c:\Users\twan\OneDrive - Danmarks Tekniske Universitet\Desktop\H4\2. MachineLearning\2.1ExampleProject"


REM Step 2: Create virtual environment

python -m venv .venv


REM Step 3: Activate virtual environment

.venv\Scripts\activate


REM Step 4: Upgrade pip

python -m pip install --upgrade pip
  

REM Step 5: Install libraries

pip install numpy pandas matplotlib scikit-learn joblib
  

REM Step 6: Run the program

python Salary_Analysis.py

```
  
---
## 📦 Library Versions (What We Installed)

| Library | Version | Purpose |

|---------|---------|---------|

| numpy | Latest | Numerical computations |

| pandas | Latest | Data manipulation |

| matplotlib | Latest | Data visualization |

| scikit-learn | Latest | Machine learning |

| joblib | Latest | Model saving |
