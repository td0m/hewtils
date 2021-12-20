import os

# make sure this directory is in the path
bin_dir = os.path.join(os.environ["HOME"], ".local/bin")

scripts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scripts")

# remove file's extension
def strip_ext(filename: str) -> str:
    return os.path.splitext(filename)[0]


if __name__ == "__main__":
    # for each file in scripts directory
    for file in os.listdir(scripts_dir):
        # if it's not a non-test python file, skip it
        if (
            not file.endswith(".py")
            or file == "__init__.py"
            or file.endswith("_test.py")
        ):
            continue

        # strip extension and copy to bin directory
        os.system(f"cp {scripts_dir}/{file} {bin_dir}/{strip_ext(file)}")
