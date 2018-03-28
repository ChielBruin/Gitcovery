# Check if the docs are correctly updated

mv REFERENCE.md REFERENCE_old.md
python docgen.py
cmp --silent REFERENCE.md REFERENCE_old.md
