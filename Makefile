PYTHON ?= $(shell command -v python3 2>/dev/null || command -v python)
DESTDIR ?= /
PODMAN_VERSION ?= $(podman version -f "{{ .Version }}")

.PHONY: python-podman
python-podman:
	PODMAN_VERSION=$(PODMAN_VERSION) \
	$(PYTHON) setup.py sdist bdist

.PHONY: lint
lint:
	$(PYTHON) -m pylint podman

.PHONY: integration
integration:
	test/test_runner.sh -v

.PHONY: install
install:
	PODMAN_VERSION=$(PODMAN_VERSION) \
	$(PYTHON) setup.py install --root ${DESTDIR}

.PHONY: upload
upload:
	PODMAN_VERSION=$(PODMAN_VERSION) $(PYTHON) setup.py sdist bdist_wheel
	twine upload --verbose dist/*
	twine upload --verbose --repository-url https://test.pypi.org/legacy/ dist/*

.PHONY: clobber
clobber: uninstall clean

.PHONY: uninstall
uninstall:
	$(PYTHON) -m pip uninstall --yes podman ||:

.PHONY: clean
clean:
	rm -rf podman.egg-info dist
	find . -depth -name __pycache__ -exec rm -rf {} \;
	find . -depth -name \*.pyc -exec rm -f {} \;
	$(PYTHON) ./setup.py clean --all
