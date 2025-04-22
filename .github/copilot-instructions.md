## General Principles

- Write code that is **readable, maintainable, and well-structured**.
- Follow the **DRY (Don’t Repeat Yourself) principle** to avoid redundancy.
- Use **descriptive variable and function names** (e.g., `calculate_total` instead of `calc`).
- Keep code **simple and concise** while ensuring clarity—**avoid over-engineering**.
- Use single quotes for **string literals** unless double quotes are needed inside the string.

## PEP 8 Compliance

- **Indentation:** Use **4 spaces** per indentation level. No tabs.
- **Line Length:** Limit lines to **79 characters**. Use parentheses (not backslashes) for line continuation.
- **Blank Lines:**
  - **2 blank lines** before top-level function and class definitions.
  - **1 blank line** between methods inside a class or logical sections within a function.
- **Whitespace:**
  - Add **one space** after commas (`func(a, b)` not `func(a,b)`).
  - Avoid extra whitespace inside parentheses (`(x + y)` not `( x + y )`).
  - Use spaces around operators (`x = 5 + 3` not `x=5+3`).
- **Naming Conventions:**
  - **Functions & variables:** `snake_case` (e.g., `get_user_data`).
  - **Classes:** `PascalCase` (e.g., `DataProcessor`).
  - **Constants:** `UPPER_CASE` (e.g., `MAX_RETRIES`).
  - **Avoid** single-letter variable names except in short loops (`for i in range(5)`).

## Code Structure

- **Imports:** Place imports at the **top** in this order:
  1. **Standard library** (e.g., `import os`)
  2. **Third-party libraries** (e.g., `import numpy as np`)
  3. **Local application modules** (e.g., `from my_module import my_function`)
  - Use **one import per line**; avoid `from module import *`.
  - **Sort imports alphabetically** within each group.
  - **Remove** unused libraries **in the import functions** to keep code clean.
- **Main Block:** Use `if __name__ == "__main__":` to prevent code from running on import.
- **Functions:**
  - Include a **docstring** explaining purpose, parameters, and return value:
    ```python
    def calculate_area(radius: float) -> float:
        """Calculate the area of a circle given the radius."""
        return 3.1416 * radius ** 2
    ```
  - Keep functions **focused**—do **one thing well**.
  - Limit function length to **20–30 lines** where possible.
- **Classes:**
  - Use **classes** when data and behavior are closely related.
  - Include an **`__init__` method** with **clear parameter names**.
  - Add a **class-level docstring** explaining its purpose.

## Type Hints

- Use **type hints** to improve clarity:

  ```python
  from typing import List, Union

  def add_numbers(a: int, b: int) -> int:
      """Add two integers and return the sum."""
      return a + b

  def get_items_list(items: List[Union[str, int]]) -> List[str]:
      """Convert all items to strings and return the new list."""
      return [str(item) for item in items]
  ```

- Annotate **both parameters and return types**.
- Consider using **Optional** for nullable parameters, and **Any** when type is unspecified.

## Error Handling

- Use `try/except` blocks to handle exceptions gracefully.
- Catch **specific exceptions** (e.g., `ValueError`) rather than generic ones.
- Include **meaningful error messages** or **log** them:
  ```python
  try:
      value = int(input("Enter a number: "))
  except ValueError:
      print("Invalid input! Please enter an integer.")
  ```

## Comments

- **Explain why**, not just **what**:
  ```python
  # Adjust threshold to avoid false positives
  threshold = 0.8
  ```
- Keep comments **concise and relevant**.
- Avoid **redundant** comments (e.g., `# Set x to 5` above `x = 5`).
- Use **inline comments sparingly** and align them.

## Code Output Formatting

- Wrap code in **triple backticks** specifying the language:
  ```python
  def example_function():
      """Example function."""
      pass
  ```
- If multiple snippets are needed, separate them with **descriptive headings** and add brief explanations before or after each snippet.

## Additional Best Practices

- **Avoid global variables**—pass data via parameters.
- Use **list comprehensions** or **generators** for concise, readable iteration:
  ```python
  squares = [x**2 for x in range(10)]
  ```
- Test **edge cases** mentally and mention them in your explanation if they’re critical.
- Use **logging** instead of `print()` in production-level code:

  ```python
  import logging

  logging.basicConfig(level=logging.INFO)
  logger = logging.getLogger(__name__)
  logger.info("Starting process...")
  ```
