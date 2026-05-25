#!/usr/bin/env python
import os
import sys

def main():
    # Path to the myapi subdirectory containing the real Django app
    myapi_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'myapi')
    
    # Insert myapi at the beginning of the path so imports resolve correctly
    sys.path.insert(0, myapi_dir)
    
    # Set default settings module
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myapi.settings")
    
    # Change current working directory to the subproject folder
    os.chdir(myapi_dir)
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
