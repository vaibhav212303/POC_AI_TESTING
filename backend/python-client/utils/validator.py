import re
import os

class PlaywrightValidator:
    def __init__(self, server_dir):
        self.server_dir = server_dir
        self.pages_dir = os.path.join(server_dir, "tests", "pages")

    def validate_spec(self, code, pom_class_name):
        errors = []
        
        # RULE: Specific Playwright Import
        # Allows "playwright/test" OR "@playwright/test" based on your setup
        if 'from "playwright/test"' not in code and 'from "@playwright/test"' not in code:
            errors.append("CRITICAL: Missing import { test, expect } from \"playwright/test\";")

        # RULE: POM Import
        if f"import {pom_class_name}Page from" not in code:
            errors.append(f"CRITICAL: Missing import for {pom_class_name}Page.")

        # RULE: Test Block
        if "test(" not in code or "await" not in code:
            errors.append("SYNTAX ERROR: Missing valid test(...) block or async/await.")

        if errors:
            return False, "\n".join(errors)
        return True, "Valid"

    def validate_pom(self, code, class_name):
        errors = []
        if f"class {class_name}Page" not in code:
            errors.append(f"SYNTAX ERROR: Expected 'class {class_name}Page'")
        
        if "readonly page" not in code and "private page" not in code:
            errors.append("LOGIC ERROR: Constructor must accept 'page'.")

        if errors:
            return False, "\n".join(errors)
        return True, "Valid"