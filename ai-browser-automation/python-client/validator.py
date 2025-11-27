import re
import os

class PlaywrightValidator:
    def __init__(self, server_dir):
        self.server_dir = server_dir
        self.pages_dir = os.path.join(server_dir, "tests", "pages")

    def validate_spec(self, code, pom_class_name):
        """
        Strictly checks the generated Spec file for common Playwright/TypeScript errors.
        Returns: (is_valid, error_message)
        """
        errors = []

        # 1. VALIDATE: The exact Playwright Import
        # Regex looks for: import { test, expect } from "@playwright/test"; (flexible on spaces/quotes)
        import_pattern = r'import\s*\{\s*test,\s*expect\s*\}\s*from\s*[\'"]@playwright/test[\'"];'
        if not re.search(import_pattern, code):
            errors.append("CRITICAL: Missing or incorrect Playwright import. Must be EXACTLY: import { test, expect } from \"playwright/test\";")

        # 2. VALIDATE: Page Object Import
        # Checks if the POM class is imported correctly
        pom_import_pattern = f"import {pom_class_name}Page from"
        if pom_import_pattern not in code:
            errors.append(f"CRITICAL: Missing import for Page Object. Expected 'import {pom_class_name}Page from ...'")

        # 3. VALIDATE: File System Check (Does the POM file actually exist?)
        # The spec tries to import '../pages/XPage'. We check if XPage.ts exists.
        expected_pom_file = f"{pom_class_name}Page.ts"
        pom_path = os.path.join(self.pages_dir, expected_pom_file)
        if not os.path.exists(pom_path):
            errors.append(f"LOGIC ERROR: The Spec imports '{expected_pom_file}', but that file was not created in {self.pages_dir}.")

        # 4. VALIDATE: Test Structure
        if "test(" not in code or "await" not in code:
            errors.append("SYNTAX ERROR: Code does not appear to contain a valid Playwright 'test(...)' block or async/await.")

        if errors:
            return False, "\n".join(errors)
        return True, "Valid"

    def validate_pom(self, code, class_name):
        """
        Strictly checks the generated Page Object Model.
        """
        errors = []

        # 1. Check Class Declaration
        if f"class {class_name}Page" not in code:
            errors.append(f"SYNTAX ERROR: Class name mismatch. Expected 'class {class_name}Page'")

        # 2. Check Playwright Import (Page type)
        if "import type { Page }" not in code and "import { type Page }" not in code:
             # Allow looser variations, but ensure Page is imported
             if "from \"@playwright/test\"" not in code:
                 errors.append("CRITICAL: Missing Playwright imports in POM.")

        # 3. Check Constructor
        if "constructor" not in code or "page" not in code:
            errors.append("LOGIC ERROR: POM must have a constructor accepting 'page'.")

        if errors:
            return False, "\n".join(errors)
        return True, "Valid"