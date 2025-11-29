import os

def get_test_files(directory="playwright-server/fixture/tests"):
    """
    Lists all .md files in the specific directory.
    """
    # specific path requested
    base_path = os.path.join(os.getcwd(), directory)
    
    if not os.path.exists(base_path):
        # Try looking one level up if run from a subdirectory
        base_path = os.path.join(os.getcwd(), "..", directory)
        if not os.path.exists(base_path):
            print(f"❌ Directory not found: {base_path}")
            return []

    return [
        os.path.join(base_path, f) 
        for f in os.listdir(base_path) 
        if f.endswith('.md')
    ]

def read_test_steps(file_path):
    """
    Reads the markdown file and returns a list of actionable steps.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Test file not found: {file_path}")

    steps = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            clean_line = line.strip()
            # We accept lines starting with -, *, or numbers (1.)
            if clean_line.startswith(('-', '*', '>')) or (clean_line and clean_line[0].isdigit() and '.' in clean_line[:4]):
                # Remove the markers (bullets or numbers)
                step_content = clean_line.lstrip("0123456789.-*> ").strip()
                if step_content:
                    steps.append(step_content)
    
    return steps