init:
	pip install -r requirements.txt

install:
	python -m pip install --upgrade pip

clean:
	# Remove all pycache
	find . | grep -E "(__pycache__|\.pyc|\.pyo$)" | xargs rm -rf

run:
	python app.py